from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from notifications.models import Notification
from .serializers import NotificationSerializer
from core.pagination import StandardResultsSetPagination
from core.serializers import ToggleStateSerializer


@extend_schema_view(
    get=extend_schema(
        tags=['Notifications'],
        summary='List my notifications',
        description='Paginated list of notifications for the authenticated user (newest first).',
    )
)
class NotificationListView(generics.ListAPIView):
    """List all notifications for the authenticated user (unread first)."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related(
            'sender', 'sender__profile', 'post', 'comment'
        )


class NotificationUnreadCountView(APIView):
    """Return count of unread notifications."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Notifications'],
        summary='Unread notification count',
        description='Returns the number of unread notifications. Also pushed live via WebSocket.',
        responses={
            200: OpenApiResponse(
                description='Unread count',
                examples=[OpenApiExample('Count', value={'unread_count': 3})],
            ),
        },
    )
    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})


class NotificationMarkReadView(APIView):
    """Mark a single notification as read."""
    permission_classes = [IsAuthenticated]
    serializer_class = ToggleStateSerializer

    @extend_schema(
        tags=['Notifications'],
        summary='Mark one notification as read',
        responses={
            200: OpenApiResponse(
                description='Marked as read',
                examples=[OpenApiExample('Read', value={'is_read': True})],
            ),
        },
    )
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user
        )
        notification.is_read = True
        notification.save()
        return Response({'is_read': True})


class NotificationMarkAllReadView(APIView):
    """Mark all notifications as read."""
    permission_classes = [IsAuthenticated]
    serializer_class = ToggleStateSerializer

    @extend_schema(
        tags=['Notifications'],
        summary='Mark all notifications as read',
        responses={
            200: OpenApiResponse(
                description='All marked as read',
                examples=[OpenApiExample('All read', value={'status': 'all notifications marked as read'})],
            ),
        },
    )
    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})
