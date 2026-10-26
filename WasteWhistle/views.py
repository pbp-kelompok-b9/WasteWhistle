from django.shortcuts import render, redirect
# decorator
from django.contrib.auth.decorators import login_required
# the method to login and logout
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.template import context

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
    
    if request.user.is_authenticated:
        return redirect("/dashboard/")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("/dashboard/")
        return response

    context = {
        "name": "Waste Whistle",
        "form": form,
    }
    return render(request, "login.html", context)

@login_required(login_url="/login/")
def dashboard(request):
    context = {
            "username":request.user.username,
            }
    return render(request, "dashboard.html", context)

def logout_user(request):
    logout(request)
    response = redirect("/")
    response.delete_cookie('last_login')
    return response
