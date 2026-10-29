from django.urls import path
from . import views

app_name = "comment"

urlpatterns = [
    path("add/", views.add_comment_ajax, name="add"),
    path("edit/<int:pk>/", views.edit_comment_ajax, name="edit"),
    path("delete/<int:pk>/", views.delete_comment_ajax, name="delete"),
]
