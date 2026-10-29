import json
import time
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from directory.models import WasteBank
from directory.forms import WasteBankForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.db import transaction


NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
WASTE_BANK_PROVINCES = (
    "Jawa Barat",
    "Jawa Tengah",
    "Jawa Timur",
    "Daerah Istimewa Yogyakarta",
    "Banten",
)


def fetch_osm_waste_banks():
    """Fetch Nominatim search results for bank sampah in the target provinces."""
    results = []
    seen_places = set()
    for province_index, province in enumerate(WASTE_BANK_PROVINCES):
        if province_index:
            time.sleep(1)

        parameters = {
            "q": f"bank sampah, {province}, Indonesia",
            "format": "jsonv2",
            "addressdetails": 1,
            "extratags": 1,
            "countrycodes": "id",
            "limit": 40,
        }
        request = Request(
            f"{NOMINATIM_SEARCH_URL}?{urlencode(parameters)}",
            headers={
                "Accept": "application/json",
                "User-Agent": "WasteWhistle/1.0 (waste-bank-directory)",
            },
        )

        with urlopen(request, timeout=5) as response:
            places = json.loads(response.read().decode("utf-8"))

        if not isinstance(places, list):
            raise ValueError("Nominatim returned an unexpected response.")

        for place in places:
            if not isinstance(place, dict):
                continue

            try:
                latitude = Decimal(str(place.get("lat"))).quantize(Decimal("0.000001"))
                longitude = Decimal(str(place.get("lon"))).quantize(Decimal("0.000001"))
            except (ArithmeticError, ValueError):
                continue

            if not (
                latitude.is_finite()
                and longitude.is_finite()
                and -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                continue

            place_key = (latitude, longitude)
            if place_key in seen_places:
                continue
            seen_places.add(place_key)

            extra_tags = place.get("extratags")
            extra_tags = extra_tags if isinstance(extra_tags, dict) else {}
            address = place.get("display_name") or "Alamat tidak tersedia"
            name = place.get("name") or address.split(",")[0]
            results.append({
                "fields": {
                    "name": name,
                    "address": address,
                    "contact_number": (
                        extra_tags.get("phone")
                        or extra_tags.get("contact:phone")
                    ),
                    "email": (
                        extra_tags.get("email")
                        or extra_tags.get("contact:email")
                    ),
                    "latitude": str(latitude),
                    "longitude": str(longitude),
                },
            })

    return results


def matches_directory_query(bank, query):
    """Apply the directory search to records from either source."""
    if not query:
        return True

    fields = bank["fields"]
    searchable_values = (
        fields.get("name"),
        fields.get("address"),
        fields.get("contact_number"),
        fields.get("email"),
    )
    normalized_query = query.casefold()
    return any(
        normalized_query in str(value).casefold()
        for value in searchable_values
        if value
    )

# Create your views here.
def show_directory(request):
    name_query = request.GET.get("name", "").strip()

    context = {
        "name_query": name_query,
        "is_staff": request.user.groups.filter(name='Staff').exists(),
        "form": WasteBankForm(),
        "active_page": "directory"
    }
    return render(request, "directory/directory_page.html", context)

@login_required(login_url="/login/")
def create_waste_bank(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    form = WasteBankForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Lokasi baru berhasil ditambahkan!")
        return redirect("directory:show_directory")

    context = {
        "form": form,
    }
    return render(request, "directory/waste_bank_form.html", context)

def get_waste_bank_json(request):
    name_query = request.GET.get("name", "").strip()
    waste_bank_list = WasteBank.objects.all()

    if name_query:
        waste_bank_list = waste_bank_list.filter(
            Q(name__icontains=name_query)
            | Q(address__icontains=name_query)
            | Q(contact_number__icontains=name_query)
            | Q(email__icontains=name_query)
        )

    data = []
    for waste_bank in waste_bank_list:
        data.append({
            "pk": str(waste_bank.id),
            "source": "osm" if waste_bank.is_osm else "manual",
            "is_manual": not waste_bank.is_osm,
            "fields": {
                "name": waste_bank.name,
                "address": waste_bank.address,
                "contact_number": waste_bank.contact_number,
                "email": waste_bank.email,
                "latitude": waste_bank.latitude,
                "longitude": waste_bank.longitude,
            }
        })
    if name_query:
        data = [bank for bank in data if matches_directory_query(bank, name_query)]
    return JsonResponse(data, safe=False)


@login_required(login_url="/login/")
@require_POST
def sync_osm_waste_banks(request):
    if not (
        request.user.is_superuser
        or request.user.groups.filter(name="Staff").exists()
    ):
        raise PermissionDenied

    try:
        osm_banks = fetch_osm_waste_banks()
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
        messages.error(request, "Gagal mengambil data bank sampah dari OpenStreetMap.")
        return redirect("directory:show_directory")

    with transaction.atomic():
        WasteBank.objects.filter(is_osm=True).delete()
        WasteBank.objects.bulk_create([
            WasteBank(**bank["fields"], is_osm=True)
            for bank in osm_banks
        ])

    messages.success(
        request,
        f"Sinkronisasi selesai: {len(osm_banks)} bank sampah dari "
        "OpenStreetMap dimuat ulang.",
    )
    return redirect("directory:show_directory")

@login_required(login_url="/login/")
def delete_waste_bank(request, waste_bank_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    waste_bank = get_object_or_404(WasteBank, pk=waste_bank_id)

    if request.method == "POST":
        waste_bank.delete()
        messages.success(request, "Lokasi berhasil dihapus!")
        return redirect("directory:show_directory")

    return redirect("directory:show_directory")

@login_required(login_url="/login/")
def edit_waste_bank(request, waste_bank_id):
    if not (request.user.is_superuser or request.user.groups.filter(name='Staff').exists()):
        raise PermissionDenied
    
    waste_bank = get_object_or_404(WasteBank, pk=waste_bank_id)
    form = WasteBankForm(request.POST or None, instance=waste_bank)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Lokasi berhasil diperbarui!")
        return redirect("directory:show_directory")

    context = {
        "form": form,
        "waste_bank": waste_bank,
    }
    return render(request, "directory/waste_bank_form.html", context)

@require_POST
def create_waste_bank_ajax(request):
    if not (request.user.is_superuser or request.user.groups.filter(name='Staff').exists()):
        return JsonResponse(
            {"message": "Hanya staf yang dapat menambahkan lokasi."},
            status=403,
        )

    form = WasteBankForm(request.POST)
    if form.is_valid():
        waste_bank = form.save()
        return JsonResponse(
            {"message": "Lokasi berhasil ditambahkan.", "pk": str(waste_bank.id)},
            status=201,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
