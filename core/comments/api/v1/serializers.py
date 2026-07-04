from rest_framework import serializers
from accounts.models import Profile
from comments.models import Comment


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['username', 'image']


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source='author.profile', read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content',
            'likes_count', 'is_liked', 'replies_count',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'author', 'created_date', 'updated_date']

    def get_likes_count(self, obj):
        if hasattr(obj, 'likes_count'):
            return obj.likes_count
        return obj.comment_likes.count()

    def get_is_liked(self, obj):
        if hasattr(obj, 'is_liked'):
            return obj.is_liked
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.comment_likes.filter(user=request.user).exists()

    def get_replies_count(self, obj):
        if hasattr(obj, 'replies_count'):
            return obj.replies_count
        return obj.replies.count()
