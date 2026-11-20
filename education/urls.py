from django.urls import path
from education.views import (
    show_edu,
    education_create_form, education_edit_form, education_item_picker, education_delete_confirm,
)

urlpatterns = [
    path("", show_edu, name="education"),
    path("manage/<slug:kind>/new/", education_create_form, name="education_create_form"),
    path("manage/<slug:kind>/items/", education_item_picker, name="education_item_picker"),
    path("manage/<slug:kind>/<uuid:pk>/edit/", education_edit_form, name="education_edit_form"),
    path("manage/<slug:kind>/<uuid:pk>/delete/confirm/", education_delete_confirm, name="education_delete_confirm"),
]
