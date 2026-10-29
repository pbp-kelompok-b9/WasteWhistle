from django.urls import path
from . import views

app_name = "comment"

urlpatterns = [
    path("add/", views.add_comment_ajax, name="add"),
    path("delete/<int:pk>/", views.delete_comment_ajax, name="delete"),
]
