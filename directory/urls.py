from django.urls import path

from directory.views import (
    show_directory,
    create_waste_bank,
    edit_waste_bank,
    delete_waste_bank,
    get_waste_bank_json,
)

app_name = "directory"

urlpatterns = [
    path("", show_directory, name="show_directory"),
    path("create_waste_bank/", create_waste_bank, name="create_waste_bank"),
    path("<uuid:waste_bank_id>/edit", edit_waste_bank, name="edit_waste_bank"),
    path("<uuid:waste_bank_id>/delete", delete_waste_bank, name="delete_waste_bank"),
    path("api/", get_waste_bank_json, name="get_waste_bank_json")
]