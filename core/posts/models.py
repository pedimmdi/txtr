from django.conf import settings
from django.db import models


class Post(models.Model):
    """A single text-only post (like a tweet)"""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.CharField(max_length=1000, blank=True)
    original_post = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reposts'
    )
    hashtags = models.ManyToManyField(
        'hashtags.Hashtag',
        blank=True,
        related_name='posts'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        if self.original_post:
            return f"{self.author} reposted post {self.original_post.id}"
        return f"{self.author} - {self.content[:30]}"


class Like(models.Model):
    """A like for a post"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='liked_posts'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
    
    def __str__(self):
        return f"{self.user} liked post {self.post.id}"


class Bookmark(models.Model):
    """Represents a user saving a post for later."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} bookmarked post {self.post.id}"
