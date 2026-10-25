from django.urls import path
from education.views import show_edu, waste_guide_api, submit_quiz_api

urlpatterns = [
    path("education/", show_edu, name="education"),
    path("api/waste-guides/",waste_guide_api, name="waste_guide_api",),
    path("api/quiz/submit/", submit_quiz_api, name="submit_quiz_api"),
]