from django.shortcuts import render
from django.utils import timezone
from education.models import WasteGuide, MythOrFact, DecompositionInfo, QuizQuestion, QuizAttempt
from django.http import JsonResponse

def show_edu(request):
    today = timezone.localdate()

    already_played = QuizAttempt.objects.filter(
        user=request.user,
        attempt_date=today
    ).exists() if request.user.is_authenticated else False

    context = {
        "already_played": already_played,
        "waste_guides": WasteGuide.objects.all(),
        "decomposition_infos": DecompositionInfo.objects.order_by("-estimated_days"),
        "myths_facts": MythOrFact.objects.all(),
    }

    if not already_played:
        context["questions"] = QuizQuestion.objects.order_by("?")[:3]

    return render(request, "education.html", context)

def waste_guide_api(request):
    query = request.GET.get("q", "").strip()
    guides = WasteGuide.objects.all()
    if query:
        guides = guides.filter(name__icontains=query)

    results = [
        {
            "id": str(guide.id),
            "name": guide.name,
            "category": guide.category,
            "description": guide.description,
            "handling_instructions": guide.handling_instruction,
        }
        for guide in guides
    ]

    return JsonResponse({"results": results})