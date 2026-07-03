from rest_framework import serializers
from accounts.models import Profile
from posts.models import Post


class AuthorSerializer(serializers.ModelSerializer):
    """Small nested view of who wrote the post"""
    class Meta:
        model = Profile
        fields = ['username', 'image']


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source='author.profile', read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content',
            'likes_count', 'is_liked',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'author', 'created_date', 'updated_date']

    def get_likes_count(self, obj):
        if hasattr(obj, 'likes_count'):
            return obj.likes_count
        return obj.likes.count()

    def get_is_liked(self, obj):
        if hasattr(obj, 'is_liked'):
            return obj.is_liked
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()
