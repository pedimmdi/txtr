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

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'created_date', 'updated_date']
        read_only_fields = ['id', 'author', 'created_date', 'updated_date']
