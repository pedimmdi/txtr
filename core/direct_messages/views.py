from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import Profile
from direct_messages.models import Conversation, Message


@login_required
def dm_list_view(request):
    """List all conversations for the current user."""
    conversations_qs = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'participants__profile', 'messages')

    conversations = []
    for conv in conversations_qs:
        other = conv.participants.exclude(id=request.user.id).first()
        if not other:
            continue

        last_msg    = conv.messages.last()
        unread_count = conv.messages.exclude(sender=request.user).filter(is_read=False).count()

        conversations.append({
            'other_username':   other.profile.username,
            'other_image':      other.profile.image.url if other.profile.image else None,
            'last_message':     last_msg.content if last_msg else None,
            'last_message_time': last_msg.created_at if last_msg else None,
            'last_sender':      last_msg.sender.profile.username if last_msg else None,
            'unread_count':     unread_count,
        })

    # Sort by most recent message
    conversations.sort(
        key=lambda c: c['last_message_time'] or conv.created_at,
        reverse=True
    )

    return render(request, 'direct_messages/list.html', {
        'conversations': conversations,
    })


@login_required
def dm_conversation_view(request, username):
    """View messages with a specific user."""
    other_profile = get_object_or_404(Profile, username=username)
    other_user    = other_profile.user

    # Get or create conversation
    existing = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()

    if not existing:
        existing = Conversation.objects.create()
        existing.participants.add(request.user, other_user)

    # Mark incoming messages as read
    existing.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

    messages_list = existing.messages.select_related(
        'sender', 'sender__profile'
    )

    return render(request, 'direct_messages/conversation.html', {
        'other_user':    other_profile,
        'messages_list': messages_list,
        'conversation':  existing,
    })
