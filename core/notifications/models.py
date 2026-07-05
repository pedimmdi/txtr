from django.conf import settings
from django.db import models


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        LIKE         = 'like',         'Like'
        COMMENT      = 'comment',      'Comment'
        REPLY        = 'reply',        'Reply'
        COMMENT_LIKE = 'comment_like', 'Comment Like'
        FOLLOW       = 'follow',       'Follow'
        REPOST       = 'repost',       'Repost'
        MENTION      = 'mention',      'Mention'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    comment = models.ForeignKey(
        'comments.Comment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_read', '-created_at']

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.notification_type}"
