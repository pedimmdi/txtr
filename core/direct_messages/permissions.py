from rest_framework.permissions import BasePermission


class IsParticipant(BasePermission):
    """Only participants of a conversation can access it."""
    def has_object_permission(self, request, view, obj):
        return request.user in obj.participants.all()


class IsSender(BasePermission):
    """Only the sender of a message can delete it."""
    def has_object_permission(self, request, view, obj):
        return obj.sender == request.user
