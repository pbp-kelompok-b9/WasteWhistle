from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def create_report(request):
    return render(request, "reporting/create.html")
