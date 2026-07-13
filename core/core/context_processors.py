# core/core/context_processors.py
# Injects global variables into every template context.


def notifications_count(request):
    """
    Adds unread_notifications_count to every template.
    The actual live count is also updated via JS polling (base.js),
    this is just for the initial server-rendered value.
    """
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}

    from notifications.models import Notification
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    return {'unread_notifications_count': count}
