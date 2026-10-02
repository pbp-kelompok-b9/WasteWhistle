from django.shortcuts import render


def landing_page(request):
    return render(request, "landing.html")

def login(request):
    return render(request, "login.html")
