from rest_framework.permissions import BasePermission


class IsCommentOwnerOrStaffDelete(BasePermission):
    message = "Anda tidak memiliki izin untuk melakukan tindakan ini pada komentar."

    def has_object_permission(self, request, view, obj):
        if request.method in ("PUT", "PATCH"):
            return obj.user == request.user
        if request.method == "DELETE":
            return (
                obj.user == request.user
                or request.user.is_staff
                or request.user.is_superuser
            )
        return True
