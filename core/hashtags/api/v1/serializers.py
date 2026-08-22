from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from hashtags.models import Hashtag


class HashtagSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Hashtag
        fields = ['name', 'posts_count']

    @extend_schema_field(OpenApiTypes.INT)
    def get_posts_count(self, obj):
        if hasattr(obj, 'posts_count'):
            return obj.posts_count
        return obj.posts.count()
