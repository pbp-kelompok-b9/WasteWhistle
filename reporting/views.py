from django.contrib import messages
from django.core import signing
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.cache import never_cache

from .forms import ReportForm
from .models import Report
from .submissions import new_submission_token, read_submission_id


@never_cache
@require_GET
def show_json(request):
    """Shared map data for signed-in users; personal history stays owner-only."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Silakan login untuk melihat laporan."}, status=401)

    reports = [
        {
            "id": report.pk,
            "title": report.title,
            "description": report.description,
            "location_note": report.location_note,
            "latitude": float(report.latitude),
            "longitude": float(report.longitude),
            "created_at": report.created_at.isoformat(),
        }
        for report in Report.objects.all()
    ]
    return JsonResponse({"reports": reports})


@login_required(login_url="login_user")
@require_GET
def report_list(request):
    reports = Report.objects.filter(reporter=request.user)
    page_obj = Paginator(reports, 10).get_page(request.GET.get("page"))
    return render(request, "reporting/list.html", {
        "page_obj": page_obj, "active_page": "reporting",
    })


@login_required(login_url="login_user")
@require_http_methods(["GET", "POST"])
def create_report(request):
    form = ReportForm(request.POST if request.method == "POST" else None)
    submission_token = request.POST.get("submission_token", "")
    submission_id = None
    submission_renewed = False
    if request.method == "POST":
        try:
            submission_id = read_submission_id(submission_token, request.user)
        except signing.BadSignature:
            submission_token = new_submission_token(request.user)
            submission_renewed = True
    else:
        submission_token = new_submission_token(request.user)
    preview = None
    if request.method == "POST" and form.is_valid():
        if request.POST.get("action") == "save":
            if submission_id is None:
                form.add_error(None, "Form perlu diperbarui. Isianmu tetap ada; periksa lalu klik Kirim laporan lagi.")
            else:
                # A database uniqueness constraint also protects simultaneous retries.
                report, created = Report.objects.get_or_create(
                    reporter=request.user, submission_id=submission_id, defaults=form.cleaned_data,
                )
                if not created and any(getattr(report, name) != value for name, value in form.cleaned_data.items()):
                    submission_token = new_submission_token(request.user)
                    submission_renewed = True
                    form.add_error(None, "Form ini sudah pernah dikirim. Klik Kirim laporan lagi untuk menyimpan isian ini sebagai laporan baru.")
                else:
                    if created:
                        messages.success(request, f"Laporan #{report.pk} berhasil disimpan.")
                    else:
                        messages.info(request, f"Laporan #{report.pk} sudah tersimpan. Tidak ada laporan tambahan yang dibuat.")
                    return redirect("reporting:list")
        else:
            preview = form.cleaned_data
    return render(request, "reporting/create.html", {
        "form": form, "preview": preview, "active_page": "reporting",
        "submission_token": submission_token,
        "submission_renewed": submission_renewed,
    })
