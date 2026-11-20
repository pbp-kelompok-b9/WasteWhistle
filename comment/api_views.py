from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Comment
from .permissions import IsCommentOwnerOrStaffDelete
from .serializers import CommentSerializer


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def comment_list(request):
    if request.method == "GET":
        comments = Comment.objects.filter(user=request.user)
        q = request.GET.get("q", "").strip()
        if q:
            comments = comments.filter(content__icontains=q)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    serializer = CommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def comment_detail(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if not IsCommentOwnerOrStaffDelete().has_object_permission(request, None, comment):
        return Response(
            {"detail": "Anda tidak memiliki izin untuk melakukan tindakan ini pada komentar."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "GET":
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    if request.method == "DELETE":
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = CommentSerializer(
        comment,
        data=request.data,
        partial=(request.method == "PATCH"),
    )
    serializer.is_valid(raise_exception=True)
    if hasattr(comment, "is_edited"):
        serializer.save(is_edited=True)
    else:
        serializer.save()
    return Response(serializer.data)
