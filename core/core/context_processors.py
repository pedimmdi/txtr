def notifications_count(request):
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'unread_messages_count': 0,
        }

    from notifications.models import Notification
    from direct_messages.models import Message

    notif_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    msg_count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()

    return {
        'unread_notifications_count': notif_count,
        'unread_messages_count': msg_count,
    }
