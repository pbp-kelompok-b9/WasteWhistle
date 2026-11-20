from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import (
    DecompositionInfo, MythOrFact, QuizAttempt, QuizQuestion, WasteGuide,
)
from .serializers import (
    DecompositionInfoSerializer, MythOrFactSerializer, QuizAnswerInputSerializer,
    QuizAttemptSerializer, QuizQuestionSerializer, WasteGuideSerializer,
)

API_AUTHENTICATION_CLASSES = [SessionAuthentication, TokenAuthentication]


class IsAdminUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return permissions.IsAdminUser().has_permission(request, view)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([IsAdminUserOrReadOnly])
def waste_guide_list(request):
    if request.method in ("GET", "HEAD"):
        guides = WasteGuide.objects.order_by("name")
        query = request.query_params.get("q", "").strip()
        if query:
            guides = guides.filter(name__icontains=query)
        serializer = WasteGuideSerializer(guides, many=True)
        return Response({"results": serializer.data})

    serializer = WasteGuideSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([IsAdminUserOrReadOnly])
def waste_guide_detail(request, pk):
    guide = get_object_or_404(WasteGuide, pk=pk)
    if request.method in ("GET", "HEAD"):
        return Response(WasteGuideSerializer(guide).data)
    if request.method == "DELETE":
        guide.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = WasteGuideSerializer(
        guide, data=request.data, partial=request.method == "PATCH",
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([IsAdminUserOrReadOnly])
def decomposition_info_list(request):
    if request.method in ("GET", "HEAD"):
        infos = DecompositionInfo.objects.order_by("estimated_days")
        return Response({"results": DecompositionInfoSerializer(infos, many=True).data})
    serializer = DecompositionInfoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([IsAdminUserOrReadOnly])
def decomposition_info_detail(request, pk):
    info = get_object_or_404(DecompositionInfo, pk=pk)
    if request.method in ("GET", "HEAD"):
        return Response(DecompositionInfoSerializer(info).data)
    if request.method == "DELETE":
        info.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = DecompositionInfoSerializer(
        info, data=request.data, partial=request.method == "PATCH",
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([IsAdminUserOrReadOnly])
def myth_or_fact_list(request):
    if request.method in ("GET", "HEAD"):
        myths = MythOrFact.objects.all()
        return Response({"results": MythOrFactSerializer(myths, many=True).data})
    serializer = MythOrFactSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([IsAdminUserOrReadOnly])
def myth_or_fact_detail(request, pk):
    item = get_object_or_404(MythOrFact, pk=pk)
    if request.method in ("GET", "HEAD"):
        return Response(MythOrFactSerializer(item).data)
    if request.method == "DELETE":
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = MythOrFactSerializer(
        item, data=request.data, partial=request.method == "PATCH",
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


def _today_quiz_response(user, start_if_missing=False):
    today = timezone.localdate()
    attempt = QuizAttempt.objects.filter(user=user, attempt_date=today).first()
    if attempt and attempt.score is not None:
        return Response({"status": "completed", "attempt": QuizAttemptSerializer(attempt).data})

    if attempt is None and start_if_missing:
        attempt = QuizAttempt.start_daily(user, today)
    if attempt is None:
        if not start_if_missing:
            return Response({"status": "not_started", "date": today})
        return Response(
            {"detail": "Kuis belum tersedia. Pastikan ada minimal tiga soal."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    questions = attempt.get_questions()
    if len(questions) != QuizAttempt.QUIZ_SIZE:
        return Response(
            {"detail": "Soal kuis tidak tersedia. Coba muat ulang."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    question_by_id = {str(question.id): question for question in questions}
    feedback = {}
    answers = attempt.answers if isinstance(attempt.answers, dict) else {}
    for question_id, chosen in answers.items():
        question = question_by_id.get(str(question_id))
        if question:
            feedback[str(question_id)] = {
                "chosen": chosen,
                "correct": chosen == question.item.category,
                "correct_bin": question.item.category,
            }
    return Response({
        "status": "in_progress",
        "quiz_id": str(attempt.id),
        "date": attempt.attempt_date,
        "total": len(questions),
        "questions": QuizQuestionSerializer(questions, many=True).data,
        "answers": feedback,
    })


@api_view(["GET"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([permissions.IsAuthenticated])
def today_quiz_api(request):
    return _today_quiz_response(request.user)


@api_view(["POST"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([permissions.IsAuthenticated])
def start_quiz_api(request):
    return _today_quiz_response(request.user, start_if_missing=True)


@api_view(["POST"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([permissions.IsAuthenticated])
def answer_question_api(request):
    today = timezone.localdate()
    attempt = QuizAttempt.objects.filter(user=request.user, attempt_date=today).first()
    if attempt is None:
        return Response(
            {"detail": "Mulai kuis terlebih dahulu lewat POST /quiz/start/."},
            status=status.HTTP_409_CONFLICT,
        )
    if attempt.score is not None:
        return Response({"detail": "Kamu sudah mengikuti kuis hari ini."}, status=status.HTTP_409_CONFLICT)

    serializer = QuizAnswerInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question_id = str(serializer.validated_data["question_id"])
    chosen = serializer.validated_data["answer"]
    if question_id not in {str(value) for value in attempt.question_ids}:
        return Response({"detail": "Soal bukan bagian dari kuis hari ini."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        attempt = QuizAttempt.objects.select_for_update().get(pk=attempt.pk)
        if attempt.score is not None:
            return Response({"detail": "Kamu sudah mengikuti kuis hari ini."}, status=status.HTTP_409_CONFLICT)
        question = get_object_or_404(
            QuizQuestion.objects.select_related("item"), pk=question_id,
        )
        if not isinstance(attempt.answers, dict):
            attempt.answers = {}
        locked_answer = attempt.answers.setdefault(question_id, chosen)
        attempt.save(update_fields=["answers"])
    return Response({
        "question_id": question_id,
        "correct": locked_answer == question.item.category,
        "correct_bin": question.item.category,
        "chosen": locked_answer,
    })


def _submit_daily_quiz(request):
    today = timezone.localdate()
    try:
        with transaction.atomic():
            attempt = QuizAttempt.objects.select_for_update().get(
                user=request.user, attempt_date=today,
            )
            if attempt.score is not None:
                return Response(QuizAttemptSerializer(attempt).data)
            question_ids = [str(value) for value in attempt.question_ids]
            if not isinstance(attempt.answers, dict) or set(attempt.answers) != set(question_ids):
                return Response(
                    {"detail": "Jawab semua soal kuis sebelum mengirim hasil."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            questions = attempt.get_questions()
            if len(questions) != QuizAttempt.QUIZ_SIZE:
                return Response(
                    {"detail": "Soal kuis berubah. Muat ulang kuis hari ini."},
                    status=status.HTTP_409_CONFLICT,
                )
            score = sum(
                attempt.answers[str(question.id)] == question.item.category
                for question in questions
            )
            attempt.score = score
            attempt.save(update_fields=["score"])
    except QuizAttempt.DoesNotExist:
        return Response(
            {"detail": "Mulai kuis terlebih dahulu lewat POST /quiz/start/."},
            status=status.HTTP_409_CONFLICT,
        )
    return Response(QuizAttemptSerializer(attempt).data)


@api_view(["GET", "POST"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([permissions.IsAuthenticated])
def quiz_attempt_list(request):
    if request.method == "POST":
        return _submit_daily_quiz(request)
    attempts = QuizAttempt.objects.filter(
        user=request.user, score__isnull=False,
    ).order_by("-attempt_date", "-id")
    return Response({"results": QuizAttemptSerializer(attempts, many=True).data})


@api_view(["POST"])
@authentication_classes(API_AUTHENTICATION_CLASSES)
@permission_classes([permissions.IsAuthenticated])
def revoke_token(request):
    if not isinstance(request.auth, Token):
        return Response(
            {"detail": "Gunakan autentikasi token untuk mencabut token."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
