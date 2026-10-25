from directory.models import *
from directory.forms import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse

# Create your views here.
def show_directory(request):
    name_query = request.GET.get("title", "").strip()
    waste_banks = WasteBank.objects.all()

    context = {
        "name_query": name_query,
        "is_staff": request.user.groups.filter(name='Staff').exists(),
        "form": WasteBankForm(),
        "waste_banks": waste_banks,
    }
    return render(request, "directory/directory.html", context)

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
    name_query = request.GET.get("title", "").strip()
    waste_bank_list = WasteBank.objects.all()

    if name_query:
        waste_bank_list = waste_bank_list.filter(title__icontains=name_query)

    data = []
    for waste_bank in waste_bank_list:

        data = []
        data.append({
            "pk": str(waste_bank.id),
            "fields": {
                "name": waste_bank.name,
                "address": waste_bank.address,
                "contact_number": waste_bank.contact_number,
                "email": waste_bank.email,
            }
        })
    return JsonResponse(data, safe=False)

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