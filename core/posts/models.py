from django.conf import settings
from django.db import models


class Post(models.Model):
    """A single text-only post (like a tweet)"""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.CharField(max_length=1000)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author} - {self.content[:30]}"
