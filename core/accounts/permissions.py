from rest_framework.permissions import BasePermission


class OnlyAnonymousUsers(BasePermission):
    """
    Allows access only to anonymous (unauthenticated) users.
    """
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return False
        return True
