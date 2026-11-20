from django.urls import path
from . import api_views

app_name = "comment_api"

urlpatterns = [
    path("comments/", api_views.comment_list, name="comment-list"),
    path("comments/<int:pk>/", api_views.comment_detail, name="comment-detail"),
]
