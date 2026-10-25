import json
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

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

    if saved and saved.get("date") == today:
        found = {
            str(question.id): question
            for question in QuizQuestion.objects.filter(
                id__in=saved["question_ids"]
            ).select_related("item")
        }
        questions = [found[i] for i in saved["question_ids"] if i in found]
        if questions:
            return questions

    questions = list(
        QuizQuestion.objects.select_related("item").order_by("?")[:QUIZ_SIZE]
    )
    request.session[SESSION_KEY] = {
        "date": today,
        "question_ids": [str(question.id) for question in questions],
    }
    return questions


def show_edu(request):
    today = timezone.localdate()

    already_played = False
    questions = []

    if request.user.is_authenticated:
        already_played = QuizAttempt.objects.filter(
            user=request.user,
            attempt_date=today,
        ).exists()

        if not already_played:
            questions = get_todays_questions(request)

    context = {
        "already_played": already_played,
        "questions": questions,
        "waste_guides": WasteGuide.objects.order_by("name"),
        "decomposition_infos": DecompositionInfo.objects.order_by("estimated_days"),
        "myths_facts": MythOrFact.objects.all(),
    }
    return render(request, "education.html", context)

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
        return JsonResponse({"error": "Please log in first."}, status=401)

    if QuizAttempt.objects.filter(user=request.user, attempt_date=today).exists():
        return JsonResponse({"error": "You already played today."}, status=409)

    saved = request.session.get(SESSION_KEY)
    if not saved or saved.get("date") != today.isoformat():
        return JsonResponse(
            {"error": "No quiz in progress. Please reload the page."}, status=400
        )

    try:
        answers = json.loads(request.body).get("answers", {})
    except (ValueError, AttributeError):
        return JsonResponse({"error": "Invalid data."}, status=400)

    if not isinstance(answers, dict):
        return JsonResponse({"error": "Invalid data."}, status=400)

    questions = list(
        QuizQuestion.objects.filter(id__in=saved["question_ids"]).select_related("item")
    )

    score = 0
    for question in questions:
        chosen_bin = answers.get(str(question.id))
        if chosen_bin == question.item.category:
            score = score + 1

    attempt, created = QuizAttempt.objects.get_or_create(
        user=request.user,
        attempt_date=today,
        defaults={"score": score},
    )

    if not created:
        return JsonResponse({"error": "You already played today."}, status=409)

    del request.session[SESSION_KEY]
    
    return JsonResponse({"score": score, "total": len(questions)})