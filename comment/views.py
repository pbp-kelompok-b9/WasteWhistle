from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .forms import CommentForm
from .models import Comment


@login_required
@require_POST
def add_comment_ajax(request):
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.save()
        return JsonResponse(
            {
                "message": "Komentar berhasil ditambahkan.",
                "id": comment.id,
                "username": comment.user.username,
                "content": comment.content,
                "is_staff": request.user.is_staff,
            },
            status=201,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


@login_required
@require_POST
def edit_comment_ajax(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if comment.user != request.user:
        return JsonResponse(
            {"message": "Anda tidak memiliki izin untuk mengedit komentar ini."},
            status=403,
        )

    form = CommentForm(request.POST, instance=comment)
    if form.is_valid():
        updated_comment = form.save(commit=False)
        # If your Comment model has an is_edited field:
        if hasattr(updated_comment, "is_edited"):
            updated_comment.is_edited = True
        updated_comment.save()

        return JsonResponse(
            {
                "message": "Komentar berhasil diperbarui.",
                "id": updated_comment.id,
                "content": updated_comment.content,
                "is_edited": True,  # <-- Passed to JS to render badge dynamically
            },
            status=200,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


@login_required
@require_POST
def delete_comment_ajax(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if not (
        comment.user == request.user
        or request.user.is_staff
        or request.user.is_superuser
    ):
        return JsonResponse(
            {"message": "Anda tidak memiliki izin untuk menghapus komentar ini."},
            status=403,
        )

    comment.delete()
    return JsonResponse({"message": "Komentar berhasil dihapus."}, status=200)
