from django.utils.html import strip_tags
from rest_framework import serializers
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    is_staff = serializers.BooleanField(source="user.is_staff", read_only=True)
    is_superuser = serializers.BooleanField(source="user.is_superuser", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "username", "is_staff", "is_superuser", "content", "created_at"]
        read_only_fields = ["id", "username", "is_staff", "is_superuser", "created_at"]

    def validate_content(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Content cannot be empty.")
        return value
