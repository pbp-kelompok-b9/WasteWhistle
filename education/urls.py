from django.urls import path
from education.views import show_edu, waste_guide_api

urlpatterns = [
    path("education/", show_edu, name="education"),
    path("api/waste-guides/",waste_guide_api, name="waste_guide_api",),
]