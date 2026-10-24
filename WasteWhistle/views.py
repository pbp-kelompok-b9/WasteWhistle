from django.shortcuts import render, redirect
# decorator
from django.contrib.auth.decorators import login_required
# the method to login and logout
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

def register_user(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("main:login_user")

    context = {
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:dashboard")
        return response

    context = {
        "name": "Waste Whistle",
        "form": form,
    }
    return render(request, "login.html", context)

@login_required(login_url="/login/")
def dashboard(request):
    return render(request, "dashboard.html")
