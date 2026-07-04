import re
from django.db.models.signals import post_save
from django.dispatch import receiver
from posts.models import Post


@receiver(post_save, sender=Post)
def extract_hashtags(sender, instance, **kwargs):
    """
    After each Post save, parse the content for #hashtag patterns,
    create Hashtag objects if they don't exist, and link them to the post.
    """
    from hashtags.models import Hashtag

    tags = set(re.findall(r'#(\w+)', instance.content.lower()))

    hashtag_objects = []
    for tag in tags:
        hashtag, _ = Hashtag.objects.get_or_create(name=tag)
        hashtag_objects.append(hashtag)

    instance.hashtags.set(hashtag_objects)
