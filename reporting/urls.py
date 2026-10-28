from django.urls import path

from . import views

app_name = "reporting"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("json/", views.show_json, name="show_json"),
    path("create/", views.create_report, name="create"),
]
