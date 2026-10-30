import json
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404

from .forms import DecompositionInfoForm, MythOrFactForm, WasteGuideForm

from education.models import (
    DecompositionInfo,
    MythOrFact,
    QuizAttempt,
    QuizQuestion,
    WasteGuide,
)

QUIZ_SIZE = 3                   
SESSION_KEY = "daily_quiz"      

EDUCATION_TYPES = {
    "guide": (WasteGuide, WasteGuideForm, "Panduan Sampah"),
    "decomposition": (DecompositionInfo, DecompositionInfoForm, "Informasi Penguraian Sampah"),
    "myth": (MythOrFact, MythOrFactForm, "Mitos atau Fakta"),
}


def get_saved_question_ids(request):
    saved = request.session.get(SESSION_KEY)
    if not isinstance(saved, dict):
        return None
    if saved.get("date") != timezone.localdate().isoformat():
        return None
    ids = saved.get("question_ids")
    if (
        isinstance(ids, list)
        and len(ids) == QUIZ_SIZE
        and all(isinstance(i, str) for i in ids)
        and len(set(ids)) == QUIZ_SIZE
    ):
        return ids
    return None

def get_todays_questions(request):
    today = timezone.localdate().isoformat()
    saved_ids = get_saved_question_ids(request)
    if saved_ids:
        found = {
            str(q.id): q
            for q in QuizQuestion.objects.filter(id__in=saved_ids).select_related("item")
        }
        questions = [found[i] for i in saved_ids if i in found]
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
        "answers": {},
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
        "quiz_size": QUIZ_SIZE,
        "waste_guides": WasteGuide.objects.order_by("name"),
        "decomposition_infos": DecompositionInfo.objects.order_by("estimated_days"),
        "myths_facts": MythOrFact.objects.all(),
    }
    return render(request, "education.html", context)


def _education_type(key):
    try:
        return EDUCATION_TYPES[key]
    except KeyError as error:
        raise Http404("Jenis konten edukasi tidak ditemukan.") from error

def _mutation_response():
    response = HttpResponse("")
    response["HX-Trigger"] = "educationContentChanged"
    return response


@login_required
@require_GET
def education_item_picker(request, kind):
    if not request.user.is_staff:
        raise PermissionDenied
    model, _, label = _education_type(kind)
    action = request.GET.get("action")
    if action not in {"edit", "delete"}:
        raise Http404("Aksi pengelolaan tidak ditemukan.")
    return render(request, "education/item_action_modal.html", {
        "key": kind,
        "label": label,
        "action": action,
        "items": model.objects.order_by("pk"),
    })


@login_required
@require_GET
def education_create_form(request, kind):
    if not request.user.is_staff:
        raise PermissionDenied
    _, form_class, label = _education_type(kind)
    return render(request, "education/content_form_modal.html", {
        "key": kind, "label": label, "form": form_class(),
    })


@login_required
@require_POST
def education_create(request, kind):
    if not request.user.is_staff:
        raise PermissionDenied
    _, form_class, _ = _education_type(kind)
    form = form_class(request.POST)
    if form.is_valid():
        form.save()
        return _mutation_response()
    return render(request, "education/content_form_modal.html", {
        "key": kind, "label": EDUCATION_TYPES[kind][2], "form": form,
    })


@login_required
@require_GET
def education_edit_form(request, kind, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    model, form_class, _ = _education_type(kind)
    item = get_object_or_404(model, pk=pk)
    return render(request, "education/content_form_modal.html", {
        "key": kind, "label": EDUCATION_TYPES[kind][2],
        "form": form_class(instance=item), "item": item,
    })


@login_required
@require_GET
def education_delete_confirm(request, kind, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    model, _, label = _education_type(kind)
    return render(request, "education/item_action_modal.html", {
        "key": kind,
        "label": label,
        "action": "confirm-delete",
        "item": get_object_or_404(model, pk=pk),
    })


@login_required
@require_POST
def education_update(request, kind, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    model, form_class, _ = _education_type(kind)
    item = get_object_or_404(model, pk=pk)
    form = form_class(request.POST, instance=item)
    if form.is_valid():
        form.save()
        return _mutation_response()
    return render(request, "education/content_form_modal.html", {
        "key": kind, "label": EDUCATION_TYPES[kind][2],
        "form": form, "item": item,
    })


@login_required
@require_POST
def education_delete(request, kind, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    model, _, _ = _education_type(kind)
    item = get_object_or_404(model, pk=pk)
    item.delete()
    return _mutation_response()


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
            "description": guide.description,
            "handling_instruction": guide.handling_instruction,
        }
        for guide in guides
    ]

    return JsonResponse({"results": results})

@require_POST
def answer_question_api(request):
    today = timezone.localdate()

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Silakan masuk terlebih dahulu."}, status=401)

    if QuizAttempt.objects.filter(user=request.user, attempt_date=today).exists():
        return JsonResponse({"error": "Kamu sudah mengikuti kuis hari ini."}, status=409)

    question_ids = get_saved_question_ids(request)
    if question_ids is None:
        return JsonResponse(
            {"error": "Kuis tidak ditemukan. Muat ulang halaman untuk mencoba lagi."},
            status=400,
        )

    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Data jawaban tidak valid."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Data jawaban tidak valid."}, status=400)

    question_id = payload.get("question_id")
    chosen = payload.get("answer")
    valid_categories = {choice[0] for choice in WasteGuide.CATEGORY_CHOICES}

    if not isinstance(question_id, str) or question_id not in question_ids:
        return JsonResponse({"error": "Soal tidak valid."}, status=400)
    if not isinstance(chosen, str) or chosen not in valid_categories:
        return JsonResponse({"error": "Pilihan tong tidak valid."}, status=400)

    question = (
        QuizQuestion.objects.select_related("item").filter(id=question_id).first()
    )
    if question is None:
        return JsonResponse({"error": "Soal tidak ditemukan."}, status=400)

    answers = request.session[SESSION_KEY].get("answers", {})
    if not isinstance(answers, dict):
        return JsonResponse({"error": "Data jawaban tidak valid."}, status=400)

    locked_answer = answers.setdefault(question_id, chosen)
    request.session[SESSION_KEY]["answers"] = answers
    request.session.modified = True

    return JsonResponse({
        "correct": locked_answer == question.item.category,
        "correct_bin": question.item.category,
        "chosen": locked_answer,
    })

@require_POST
def submit_quiz_api(request):
    today = timezone.localdate()

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Silakan masuk terlebih dahulu."}, status=401)

    if QuizAttempt.objects.filter(user=request.user, attempt_date=today).exists():
        return JsonResponse({"error": "Kamu sudah mengikuti kuis hari ini."}, status=409)

    question_ids = get_saved_question_ids(request)
    if question_ids is None:
        return JsonResponse(
            {"error": "Kuis tidak ditemukan. Muat ulang halaman untuk mencoba lagi."},
            status=400,
        )

    answers = request.session[SESSION_KEY].get("answers", {})
    if not isinstance(answers, dict) or set(answers) != set(question_ids):
        return JsonResponse(
            {"error": "Jawab semua soal kuis sebelum mengirim hasil."}, status=400
        )

    questions = list(
        QuizQuestion.objects.filter(id__in=question_ids).select_related("item")
    )
    if len(questions) != QUIZ_SIZE:
        request.session.pop(SESSION_KEY, None)
        return JsonResponse(
            {"error": "Soal kuis berubah. Muat ulang halaman untuk mencoba lagi."},
            status=400,
        )

    score = 0
    for question in questions:
        if answers.get(str(question.id)) == question.item.category:
            score += 1

    _, created = QuizAttempt.objects.get_or_create(
        user=request.user,
        attempt_date=today,
        defaults={"score": score},
    )
    if not created:
        return JsonResponse({"error": "Kamu sudah mengikuti kuis hari ini."}, status=409)

    del request.session[SESSION_KEY]
    return JsonResponse({"score": score, "total": len(questions)})
