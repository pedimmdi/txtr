from django.db.models import Count
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from hashtags.models import Hashtag
from hashtags.api.v1.serializers import HashtagSerializer
from posts.api.v1.views import get_annotated_posts
from posts.api.v1.serializers import PostSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class HashtagListView(generics.ListAPIView):
    """
    List all hashtags ordered by post count (trending first).
    """
    serializer_class = HashtagSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Hashtag.objects.annotate(
            posts_count=Count('posts')
        ).order_by('-posts_count')


class HashtagPostsView(generics.ListAPIView):
    """
    List all posts tagged with a specific hashtag.
    """
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    search_fields = ['content']
    ordering_fields = ['created_date', 'likes_count']

    def get_queryset(self):
        hashtag = get_object_or_404(Hashtag, name=self.kwargs['name'].lower())
        return get_annotated_posts(self.request.user).filter(hashtags=hashtag)
