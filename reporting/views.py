from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_http_methods

from .forms import ReportForm
from .models import Report


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
    preview = None
    if request.method == "POST" and form.is_valid():
        if request.POST.get("action") == "save":
            Report.objects.create(reporter=request.user, **form.cleaned_data)
            messages.success(request, "Laporan berhasil disimpan.")
            return redirect("reporting:list")
        preview = form.cleaned_data
    return render(request, "reporting/create.html", {
        "form": form, "preview": preview, "active_page": "reporting",
    })
