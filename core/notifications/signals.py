import re


_old_content_cache = {}


def extract_mentions(content):
    """Extract all @username patterns from text."""
    return set(re.findall(r'@(\w+)', content.lower()))


def cache_old_content(sender, instance, **kwargs):
    """
    pre_save: before saving, cache the old content.
    This runs before the new data is written to DB.
    """
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
        _old_content_cache[f"{sender.__name__}_{instance.pk}"] = old.content
    except sender.DoesNotExist:
        pass


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
        if instance.author != instance.post.author:
            Notification.objects.create(
                recipient=instance.post.author,
                sender=instance.author,
                notification_type=Notification.NotificationType.COMMENT,
                post=instance.post,
                comment=instance
            )
    else:
        if instance.author != instance.parent.author:
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


def notify_repost(sender, instance, created, **kwargs):
    """Fires when a Post with original_post set is created."""
    if not created:
        return
    if instance.original_post is None:
        return
    from notifications.models import Notification
    Notification.objects.create(
        recipient=instance.original_post.author,
        sender=instance.author,
        notification_type=Notification.NotificationType.REPOST,
        post=instance.original_post
    )


def notify_mentions(sender, instance, created, **kwargs):
    """
    post_save: compare new mentions with old mentions.
    Only notify for newly added @mentions.
    """
    from notifications.models import Notification
    from accounts.models import Profile

    new_mentions = extract_mentions(instance.content)

    if created:
        mentions_to_notify = new_mentions
    else:
        cache_key = f"{sender.__name__}_{instance.pk}"
        old_content = _old_content_cache.pop(cache_key, '')
        old_mentions = extract_mentions(old_content)
        mentions_to_notify = new_mentions - old_mentions

    if not mentions_to_notify:
        return

    is_post = hasattr(instance, 'original_post')

    for username in mentions_to_notify:
        try:
            profile = Profile.objects.select_related('user').get(username=username)
            mentioned_user = profile.user
        except Profile.DoesNotExist:
            continue

        if mentioned_user == instance.author:
            continue

        Notification.objects.create(
            recipient=mentioned_user,
            sender=instance.author,
            notification_type=Notification.NotificationType.MENTION,
            post=instance if is_post else instance.post,
            comment=None if is_post else instance,
        )
