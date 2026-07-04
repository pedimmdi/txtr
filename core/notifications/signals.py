def notify_post_like(sender, instance, created, **kwargs):
    """Fires when a Like object is created."""
    if not created:
        return
    if instance.user == instance.post.author:
        return
    from notifications.models import Notification
    Notification.objects.create(
        recipient=instance.post.author,
        sender=instance.user,
        notification_type=Notification.NotificationType.LIKE,
        post=instance.post
    )


def notify_comment_or_reply(sender, instance, created, **kwargs):
    """Fires when a Comment object is created (comment or reply)."""
    if not created:
        return
    from notifications.models import Notification

    if instance.parent is None:
        if instance.author == instance.post.author:
            return
        Notification.objects.create(
            recipient=instance.post.author,
            sender=instance.author,
            notification_type=Notification.NotificationType.COMMENT,
            post=instance.post,
            comment=instance
        )
    else:
        if instance.author == instance.parent.author:
            return
        Notification.objects.create(
            recipient=instance.parent.author,
            sender=instance.author,
            notification_type=Notification.NotificationType.REPLY,
            post=instance.post,
            comment=instance
        )


def notify_comment_like(sender, instance, created, **kwargs):
    """Fires when a CommentLike object is created."""
    if not created:
        return
    if instance.user == instance.comment.author:
        return
    from notifications.models import Notification
    Notification.objects.create(
        recipient=instance.comment.author,
        sender=instance.user,
        notification_type=Notification.NotificationType.COMMENT_LIKE,
        post=instance.comment.post,
        comment=instance.comment
    )


def notify_follow(sender, instance, created, **kwargs):
    """Fires when a Follow object is created."""
    if not created:
        return
    from notifications.models import Notification
    Notification.objects.create(
        recipient=instance.following,
        sender=instance.follower,
        notification_type=Notification.NotificationType.FOLLOW
    )
