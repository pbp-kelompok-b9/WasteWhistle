from django.urls import path
from directory import api_views

app_name = "api"
urlpatterns = [
    path("wastebanks/", api_views.wastebank_list, name="wastebank-list"),
    path("wastebanks/<uuid:wastebank_id>/", api_views.wastebank_detail, name="wastebank-detail"),
]