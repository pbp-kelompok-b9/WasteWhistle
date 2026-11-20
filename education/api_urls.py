from django.urls import path
from rest_framework.authtoken.views import ObtainAuthToken
from education import api_views

urlpatterns = [
    path("auth/token/", ObtainAuthToken.as_view(), name="api_token_auth"),
    path("auth/token/revoke/", api_views.revoke_token, name="api_token_revoke"),
    path("waste-guides/", api_views.waste_guide_list, name="waste_guide_api"),
    path("waste-guides/<uuid:pk>/", api_views.waste_guide_detail, name="waste_guide_detail_api"),
    path("decomposition-infos/", api_views.decomposition_info_list, name="decomposition_info_api"),
    path("decomposition-infos/<uuid:pk>/", api_views.decomposition_info_detail, name="decomposition_info_detail_api"),
    path("myths-facts/", api_views.myth_or_fact_list, name="myth_or_fact_api"),
    path("myths-facts/<uuid:pk>/", api_views.myth_or_fact_detail, name="myth_or_fact_detail_api"),
    path("quiz/today/", api_views.today_quiz_api, name="today_quiz_api"),
    path("quiz/start/", api_views.start_quiz_api, name="start_quiz_api"),
    path("quiz/answer/", api_views.answer_question_api, name="answer_question_api"),
    path("quiz/attempts/", api_views.quiz_attempt_list, name="quiz_attempt_list_api"),
]
