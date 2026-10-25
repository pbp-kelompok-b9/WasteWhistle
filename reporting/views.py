from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import ReportForm


@require_http_methods(["GET", "POST"])
def create_report(request):
    form = ReportForm(request.POST if request.method == "POST" else None)
    preview = form.cleaned_data if request.method == "POST" and form.is_valid() else None
    return render(request, "reporting/create.html", {"form": form, "preview": preview})
