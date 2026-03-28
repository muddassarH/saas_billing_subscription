from rest_framework.permissions import BasePermission

from accounts.models import UserRole


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.role == UserRole.ADMIN or u.is_superuser))
