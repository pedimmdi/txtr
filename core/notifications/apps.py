from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        from django.db.models.signals import post_save, pre_save
        from posts.models import Like, Post
        from comments.models import Comment, CommentLike
        from accounts.models import Follow
        from notifications.signals import (
            notify_post_like,
            notify_comment_or_reply,
            notify_comment_like,
            notify_follow,
            notify_repost,
            notify_mentions,
            cache_old_content,
        )

        post_save.connect(notify_post_like, sender=Like)
        post_save.connect(notify_comment_or_reply, sender=Comment)
        post_save.connect(notify_comment_like, sender=CommentLike)
        post_save.connect(notify_follow, sender=Follow)
        post_save.connect(notify_repost, sender=Post)

        pre_save.connect(cache_old_content, sender=Post)
        pre_save.connect(cache_old_content, sender=Comment)
        post_save.connect(notify_mentions, sender=Post)
        post_save.connect(notify_mentions, sender=Comment)
