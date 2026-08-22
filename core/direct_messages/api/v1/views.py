from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from accounts.models import Profile
from core.consumers import dm_room_name
from core.pagination import StandardResultsSetPagination
from direct_messages.models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


def broadcast_dm_message(user_a_id, user_b_id, serialized_message):
    """
    Push a serialized message to the shared DM room so open WebSocket
    clients receive it without polling.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    room = dm_room_name(user_a_id, user_b_id)
    async_to_sync(channel_layer.group_send)(
        room,
        {
            'type': 'chat.message',
            'message': {
                'type': 'chat.message',
                'message': serialized_message,
            },
        },
    )


class ConversationListView(APIView):
    """GET: list all conversations for the current user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Direct Messages'],
        summary='List my conversations',
        description='Returns all conversations the authenticated user participates in.',
        responses={200: ConversationSerializer(many=True)},
        operation_id='dm_conversations_list',
    )
    def get(self, request):
        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'participants__profile', 'messages')
        serializer = ConversationSerializer(
            conversations, many=True, context={'request': request}
        )
        return Response(serializer.data)


class ConversationDetailView(APIView):
    """
    GET: view messages with a specific user.
         Creates the conversation if it doesn't exist yet.
    POST: send a message to a specific user.
          Creates the conversation if it doesn't exist yet.
    """

    permission_classes = [IsAuthenticated]

    def get_or_create_conversation(self, request, username):
        """Helper: return existing conversation or create a new one."""
        profile = get_object_or_404(Profile, username=username)
        other_user = profile.user

        if other_user == request.user:
            return None, None, Response(
                {'error': 'You cannot message yourself'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()

        if existing:
            return existing, other_user, None

        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        return conversation, other_user, None

    @extend_schema(
        tags=['Direct Messages'],
        summary='Get conversation messages',
        description=(
            'Paginated messages with the given username. '
            'Creates the conversation if it does not exist. '
            'Marks incoming messages as read.'
        ),
        responses={200: MessageSerializer(many=True)},
        operation_id='dm_conversation_messages',
    )
    def get(self, request, username):
        conversation, other_user, error = self.get_or_create_conversation(
            request, username
        )
        if error:
            return error

        conversation.messages.exclude(
            sender=request.user
        ).filter(
            is_read=False
        ).update(is_read=True)

        messages = conversation.messages.select_related(
            'sender',
            'sender__profile',
            'reply_to',
            'reply_to__sender__profile',
            'forwarded_post',
            'forwarded_post__author__profile',
            'forwarded_post__original_post',
            'forwarded_post__original_post__author__profile',
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(messages, request)
        serializer = MessageSerializer(
            page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=['Direct Messages'],
        summary='Send a direct message',
        description=(
            'Send a message to the given username. '
            'Supports plain text, reply_to (message id) and forwarded_post (post id). '
            'Message is also pushed live via WebSocket.'
        ),
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'content': {'type': 'string', 'description': 'Message text'},
                    'reply_to': {'type': 'integer', 'description': 'ID of message being replied to'},
                    'forwarded_post': {'type': 'integer', 'description': 'ID of post to forward'},
                },
            }
        },
        responses={
            201: MessageSerializer,
            400: OpenApiResponse(description='Validation error'),
        },
    )
    def post(self, request, username):
        conversation, other_user, error = self.get_or_create_conversation(
            request, username
        )
        if error:
            return error

        content = (request.data.get('content') or '').strip()
        reply_to_id = request.data.get('reply_to') or request.data.get('reply_to_id')
        forwarded_post_id = (
            request.data.get('forwarded_post')
            or request.data.get('forwarded_post_id')
        )

        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(
                    pk=int(reply_to_id),
                    conversation=conversation,
                )
            except (Message.DoesNotExist, TypeError, ValueError):
                return Response(
                    {'error': 'reply_to message not found in this conversation'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        forwarded_post = None
        if forwarded_post_id:
            from posts.models import Post

            try:
                forwarded_post = Post.objects.select_related(
                    'author',
                    'author__profile',
                    'original_post',
                    'original_post__author__profile',
                ).get(pk=int(forwarded_post_id))
            except (Post.DoesNotExist, TypeError, ValueError):
                return Response(
                    {'error': 'forwarded_post not found'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not content and not forwarded_post:
            return Response(
                {'error': 'content or forwarded_post is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            reply_to=reply_to,
            forwarded_post=forwarded_post,
        )
        # Touch updated_at
        conversation.save()

        serializer = MessageSerializer(message, context={'request': request})
        data = serializer.data

        # Realtime: notify both open sockets in this DM room
        broadcast_dm_message(request.user.id, other_user.id, data)

        return Response(data, status=status.HTTP_201_CREATED)


class MessageDeleteView(APIView):
    """DELETE a message — only the sender can delete."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Direct Messages'],
        summary='Delete a message',
        description='Delete a message. Only the sender can delete their own messages.',
        responses={
            204: OpenApiResponse(description='Message deleted'),
            403: OpenApiResponse(description='Not the sender'),
            404: OpenApiResponse(description='Conversation or message not found'),
        },
    )
    def delete(self, request, username, pk):
        profile = get_object_or_404(Profile, username=username)
        other_user = profile.user
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        if not conversation:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        message = get_object_or_404(
            Message,
            pk=pk,
            conversation=conversation,
        )
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN,
            )
        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
