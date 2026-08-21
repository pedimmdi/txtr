"""
WebSocket consumers for txtr.
"""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

User = get_user_model()


def dm_room_name(user_id_a, user_id_b):
    """Stable room name for a pair of users (order-independent)."""
    low, high = sorted([int(user_id_a), int(user_id_b)])
    return f'dm_{low}_{high}'


class PingConsumer(AsyncWebsocketConsumer):
    """Connectivity check: client sends ping, server replies pong."""

    async def connect(self):
        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            await self.close()
            return
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'detail': 'Invalid JSON',
            }))
            return

        if payload.get('type') == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'message': payload.get('message', 'ok'),
            }))


class DMConsumer(AsyncWebsocketConsumer):
    """
    Realtime delivery for a conversation with one other user.

    URL: ws/dm/<username>/
    Client must be authenticated; username is the other participant.
    """

    async def connect(self):
        self.user = self.scope.get('user')
        if self.user is None or self.user.is_anonymous:
            await self.close()
            return

        self.other_username = self.scope['url_route']['kwargs']['username']
        self.other_user = await self._get_user_by_username(self.other_username)
        if self.other_user is None or self.other_user.id == self.user.id:
            await self.close()
            return

        self.room_name = dm_room_name(self.user.id, self.other_user.id)
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Optional: client can send chat.ping to keep-alive.
        Actual message create stays on the REST API for validation.
        """
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if payload.get('type') == 'chat.ping':
            await self.send(text_data=json.dumps({'type': 'chat.pong'}))

    async def chat_message(self, event):
        """
        Handler name must match the 'type' in group_send:
        {'type': 'chat.message', ...} → chat_message
        """
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def _get_user_by_username(self, username):
        from accounts.models import Profile
        try:
            return Profile.objects.select_related('user').get(username=username).user
        except Profile.DoesNotExist:
            return None


def notifications_group(user_id):
    """Personal notification channel for one user."""
    return f'notifications_{int(user_id)}'


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Pushes unread notification counts to the logged-in user.

    URL: ws/notifications/
    """

    async def connect(self):
        self.user = self.scope.get('user')
        if self.user is None or self.user.is_anonymous:
            await self.close()
            return

        self.group_name = notifications_group(self.user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current count immediately on connect
        count = await self._unread_count()
        await self.send(text_data=json.dumps({
            'type': 'notifications.unread',
            'unread_count': count,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def notifications_unread(self, event):
        """Handles group_send type 'notifications.unread'."""
        await self.send(text_data=json.dumps({
            'type': 'notifications.unread',
            'unread_count': event.get('unread_count', 0),
        }))

    @database_sync_to_async
    def _unread_count(self):
        from notifications.models import Notification
        return Notification.objects.filter(
            recipient_id=self.user.id,
            is_read=False,
        ).count()
