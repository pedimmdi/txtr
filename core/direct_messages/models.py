from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """A private conversation between exactly two users."""
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id}"


class Message(models.Model):
    """A single message inside a conversation."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.CharField(max_length=1000, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Reply to another message in the same conversation
    reply_to = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replies'
    )

    # Optional forwarded post card
    forwarded_post = models.ForeignKey(
        'posts.Post',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='forwarded_in_messages'
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        preview = self.content[:30] if self.content else '[forwarded post]'
        return f"{self.sender} → conversation {self.conversation.id}: {preview}"
