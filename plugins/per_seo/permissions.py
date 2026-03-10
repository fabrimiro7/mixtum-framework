from rest_framework.permissions import BasePermission


class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if hasattr(user, "is_at_least_associate") and callable(user.is_at_least_associate):
            return user.is_at_least_associate()
        return getattr(user, "permission", 0) >= 50
