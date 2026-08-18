from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from accounts.models import Profile
from direct_messages.models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from core.pagination import StandardResultsSetPagination


class ConversationListView(APIView):
    """GET: list all conversations for the current user."""
    permission_classes = [IsAuthenticated]

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
            return None, Response(
                {'error': 'You cannot message yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()

        if existing:
            return existing, None

        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        return conversation, None

    def get(self, request, username):
        conversation, error = self.get_or_create_conversation(request, username)
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
        serializer = MessageSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, username):
        conversation, error = self.get_or_create_conversation(request, username)
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
                    conversation=conversation
                )
            except (Message.DoesNotExist, TypeError, ValueError):
                return Response(
                    {'error': 'reply_to message not found in this conversation'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        forwarded_post = None
        if forwarded_post_id:
            from posts.models import Post
            try:
                forwarded_post = Post.objects.select_related(
                    'author', 'author__profile', 'original_post', 'original_post__author__profile'
                ).get(pk=int(forwarded_post_id))
            except (Post.DoesNotExist, TypeError, ValueError):
                return Response(
                    {'error': 'forwarded_post not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if not content and not forwarded_post:
            return Response(
                {'error': 'content or forwarded_post is required'},
                status=status.HTTP_400_BAD_REQUEST
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageDeleteView(APIView):
    """DELETE a message — only the sender can delete."""
    permission_classes = [IsAuthenticated]

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
                status=status.HTTP_404_NOT_FOUND
            )

        message = get_object_or_404(
            Message,
            pk=pk,
            conversation=conversation
        )

        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )

        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
