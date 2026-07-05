from rest_framework import serializers
from accounts.models import Profile
from posts.models import Post


class AuthorSerializer(serializers.ModelSerializer):
    """Small nested view of who wrote the post"""
    class Meta:
        model = Profile
        fields = ['username', 'image']


class OriginalPostSerializer(serializers.ModelSerializer):
    """
    A simple, flat serializer for the original post inside a repost.
    Non-recursive — does not nest further.
    """
    author = AuthorSerializer(source='author.profile', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'created_date']


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source='author.profile', read_only=True)
    original_post = OriginalPostSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    is_reposted = serializers.SerializerMethodField()
    reposts_count = serializers.SerializerMethodField()
    hashtags = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'original_post', 'hashtags',
            'likes_count', 'is_liked', 'is_bookmarked',
            'reposts_count', 'is_reposted',
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

    def get_is_bookmarked(self, obj):
        if hasattr(obj, 'is_bookmarked'):
            return obj.is_bookmarked
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarks.filter(user=request.user).exists()

    def get_reposts_count(self, obj):
        if hasattr(obj, 'reposts_count'):
            return obj.reposts_count
        return obj.reposts.count()

    def get_is_reposted(self, obj):
        if hasattr(obj, 'is_reposted'):
            return obj.is_reposted
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Post.objects.filter(
            author=request.user,
            original_post=obj
        ).exists()

    def get_hashtags(self, obj):
        return [tag.name for tag in obj.hashtags.all()]
