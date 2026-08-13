from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from notifications.models import Notification


@login_required
def notification_list_view(request):
    """Notification list — unread first, then newest."""
    notifications_qs = Notification.objects.filter(
        recipient=request.user
    ).select_related(
        'sender', 'sender__profile', 'post', 'comment'
    )

    paginator     = Paginator(notifications_qs, 30)
    notifications = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'notifications/list.html', {
        'notifications': notifications,
    })
