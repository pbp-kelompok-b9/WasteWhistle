from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .forms import DecompositionInfoForm, MythOrFactForm, WasteGuideForm

from education.models import (
    DecompositionInfo,
    MythOrFact,
    QuizAttempt,
    WasteGuide,
)

QUIZ_SIZE = QuizAttempt.QUIZ_SIZE

EDUCATION_TYPES = {
    "guide": (WasteGuide, WasteGuideForm, "Panduan Sampah"),
    "decomposition": (DecompositionInfo, DecompositionInfoForm, "Informasi Penguraian Sampah"),
    "myth": (MythOrFact, MythOrFactForm, "Mitos atau Fakta"),
}

EDUCATION_API_NAMES = {
    "guide": ("waste_guide_api", "waste_guide_detail_api"),
    "decomposition": ("decomposition_info_api", "decomposition_info_detail_api"),
    "myth": ("myth_or_fact_api", "myth_or_fact_detail_api"),
}


def _api_url(kind, pk=None):
    name = EDUCATION_API_NAMES[kind][1] if pk else EDUCATION_API_NAMES[kind][0]
    return reverse(name, kwargs={"pk": pk}) if pk else reverse(name)


def get_todays_questions(request):
    attempt = QuizAttempt.start_daily(request.user, timezone.localdate())
    if attempt is None or attempt.score is not None:
        return []
    return attempt.get_questions()


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
        "key": kind, "label": label, "form": form_class(), "api_url": _api_url(kind),
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
        "form": form_class(instance=item), "item": item, "api_url": _api_url(kind, item.pk),
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
        "api_url": _api_url(kind, pk),
    })
