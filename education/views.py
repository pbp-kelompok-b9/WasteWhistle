import json
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from education.models import (
    DecompositionInfo,
    MythOrFact,
    QuizAttempt,
    QuizQuestion,
    WasteGuide,
)

QUIZ_SIZE = 3                   
SESSION_KEY = "daily_quiz"      


def get_todays_questions(request):
    today = timezone.localdate().isoformat()
    saved = request.session.get(SESSION_KEY)

    if (
        isinstance(saved, dict)
        and saved.get("date") == today
        and isinstance(saved.get("question_ids"), list)
        and len(saved["question_ids"]) == QUIZ_SIZE
        and all(isinstance(question_id, str) for question_id in saved["question_ids"])
        and len(set(saved["question_ids"])) == QUIZ_SIZE
    ):
        found = {
            str(question.id): question
            for question in QuizQuestion.objects.filter(
                id__in=saved["question_ids"]
            ).select_related("item")
        }
        questions = [found[i] for i in saved["question_ids"] if i in found]
        if len(questions) == QUIZ_SIZE:
            return questions

    questions = list(
        QuizQuestion.objects.select_related("item").order_by("?")[:QUIZ_SIZE]
    )
    if len(questions) != QUIZ_SIZE:
        request.session.pop(SESSION_KEY, None)
        return []

    request.session[SESSION_KEY] = {
        "date": today,
        "question_ids": [str(question.id) for question in questions],
    }
    return questions


def show_edu(request):
    today = timezone.localdate()

    already_played = False
    daily_score = None
    questions = []

    if request.user.is_authenticated:
        daily_score = QuizAttempt.objects.filter(
            user=request.user,
            attempt_date=today,
        ).values_list("score", flat=True).first()
        already_played = daily_score is not None

        if not already_played:
            questions = get_todays_questions(request)

    context = {
        "active_page": "education",
        "already_played": already_played,
        "daily_score": daily_score,
        "questions": questions,
        "waste_guides": WasteGuide.objects.order_by("name"),
        "decomposition_infos": DecompositionInfo.objects.order_by("estimated_days"),
        "myths_facts": MythOrFact.objects.all(),
    }
    return render(request, "education.html", context)

@require_GET
def waste_guide_api(request):
    query = request.GET.get("q", "").strip()
    guides = WasteGuide.objects.order_by("name")

    if query:
        guides = guides.filter(name__icontains=query)

    results = [
        {
            "id": str(guide.id),
            "name": guide.name,
            "category": guide.category,                        
            "category_display": guide.get_category_display(),  
            "description": guide.description,
            "handling_instruction": guide.handling_instruction,
        }
        for guide in guides
    ]

    return JsonResponse({"results": results})

@require_POST
def submit_quiz_api(request):
    today = timezone.localdate()

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Silakan masuk terlebih dahulu."}, status=401)

    if QuizAttempt.objects.filter(user=request.user, attempt_date=today).exists():
        return JsonResponse({"error": "Kamu sudah mengikuti kuis hari ini."}, status=409)

    saved = request.session.get(SESSION_KEY)
    question_ids = saved.get("question_ids") if isinstance(saved, dict) else None
    if (
        not isinstance(saved, dict)
        or saved.get("date") != today.isoformat()
        or not isinstance(question_ids, list)
        or len(question_ids) != QUIZ_SIZE
        or not all(isinstance(question_id, str) for question_id in question_ids)
        or len(set(question_ids)) != QUIZ_SIZE
    ):
        return JsonResponse(
            {"error": "Kuis tidak ditemukan. Muat ulang halaman untuk mencoba lagi."}, status=400
        )

    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Data kuis tidak valid."}, status=400)

    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(answers, dict):
        return JsonResponse({"error": "Data jawaban tidak valid."}, status=400)

    questions = list(
        QuizQuestion.objects.filter(id__in=question_ids).select_related("item")
    )
    if len(questions) != QUIZ_SIZE:
        request.session.pop(SESSION_KEY, None)
        return JsonResponse(
            {"error": "Soal kuis berubah. Muat ulang halaman untuk mencoba lagi."},
            status=400,
        )

    question_ids = {str(question.id) for question in questions}
    valid_categories = {choice[0] for choice in WasteGuide.CATEGORY_CHOICES}
    if set(answers) != question_ids or any(
        not isinstance(answer, str) or answer not in valid_categories
        for answer in answers.values()
    ):
        return JsonResponse(
            {"error": "Jawab semua soal kuis sebelum mengirim hasil."}, status=400
        )

    score = 0
    for question in questions:
        chosen_bin = answers.get(str(question.id))
        if chosen_bin == question.item.category:
            score = score + 1

    _, created = QuizAttempt.objects.get_or_create(
        user=request.user,
        attempt_date=today,
        defaults={"score": score},
    )

    if not created:
        return JsonResponse({"error": "Kamu sudah mengikuti kuis hari ini."}, status=409)

    del request.session[SESSION_KEY]
    
    return JsonResponse({"score": score, "total": len(questions)})
