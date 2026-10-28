from django.shortcuts import render, redirect
# decorator
from django.contrib.auth.decorators import login_required
# the method to login and logout
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from reporting.models import Report

def register_user(request):

    if request.user.is_authenticated:
        return redirect("/dashboard/")

    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("/login/")

    context = {
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = reverse("dashboard")

    if request.user.is_authenticated:
        return redirect(next_url)

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect(next_url)
        return response

    context = {
        "name": "Waste Whistle",
        "form": form,
        "next": next_url,
    }
    return render(request, "login.html", context)

@login_required(login_url="/login/")
def dashboard(request):
# Calculate real statistics from Report model
    total_reports = Report.objects.count()
    user_reports_count = Report.objects.filter(reporter=request.user).count()
    user_points = user_reports_count * 10  # e.g., 10 points per report submitted

    # Fetch 10 most recent reports with reporter user data attached
    dispatch_logs = Report.objects.select_related('reporter').order_by('-created_at')[:10]

    context = {
        'active_page': 'dashboard',
        'username': request.user.username,
        'stat_open_spots': total_reports,
        'stat_points': user_points,
        'stat_points_detail': f"{user_reports_count} laporan dikirim",
        'dispatch_logs': dispatch_logs,
    }
    return render(request, 'dashboard.html', context)

def logout_user(request):
    logout(request)
    response = redirect("/")
    response.delete_cookie('last_login')
    return response
