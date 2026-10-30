from django.urls import path
from education.views import (
    show_edu, waste_guide_api, submit_quiz_api, answer_question_api,
    education_create, education_create_form, education_edit_form, education_update,
    education_delete, education_item_picker, education_delete_confirm,
)

urlpatterns = [
    path("", show_edu, name="education"),
    path("api/waste-guides/",waste_guide_api, name="waste_guide_api",),
    path("api/quiz/submit/", submit_quiz_api, name="submit_quiz_api"),
    path("api/quiz/answer/", answer_question_api, name="answer_question_api"),
    path("manage/<slug:kind>/create/", education_create, name="education_create"),
    path("manage/<slug:kind>/new/", education_create_form, name="education_create_form"),
    path("manage/<slug:kind>/items/", education_item_picker, name="education_item_picker"),
    path("manage/<slug:kind>/<uuid:pk>/edit/", education_edit_form, name="education_edit_form"),
    path("manage/<slug:kind>/<uuid:pk>/delete/confirm/", education_delete_confirm, name="education_delete_confirm"),
    path("manage/<slug:kind>/<uuid:pk>/update/", education_update, name="education_update"),
    path("manage/<slug:kind>/<uuid:pk>/delete/", education_delete, name="education_delete"),
]
