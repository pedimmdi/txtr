from rest_framework import serializers
from hashtags.models import Hashtag


class HashtagSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Hashtag
        fields = ['name', 'posts_count']

    def get_posts_count(self, obj):
        if hasattr(obj, 'posts_count'):
            return obj.posts_count
        return obj.posts.count()
