from django.db.models import Count, Exists, OuterRef
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
)
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from accounts.models import Profile, Follow
from posts.models import Post, Like, Bookmark
from posts.permissions import IsAuthorOrReadOnly
from core.throttles import PostCreateRateThrottle, LikeRateThrottle
from .serializers import PostSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


def get_annotated_posts(user):
    """
    Returns a Post queryset annotated with likes_count and is_liked.
    Solves the N+1 query problem.
    """
    qs = Post.objects.select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'hashtags'
    ).annotate(
        likes_count=Count('likes', distinct=True)
    )
    if user and user.is_authenticated:
        user_likes = Like.objects.filter(post=OuterRef('pk'), user=user)
        user_bookmarks = Bookmark.objects.filter(post=OuterRef('pk'), user=user)
        qs = qs.annotate(
            is_liked=Exists(user_likes),
            is_bookmarked=Exists(user_bookmarks),
        )
    return qs


class PostListCreateView(generics.ListCreateAPIView):
    """GET: public list of all posts. POST: create a post as request.user."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    search_fields = ['content']
    ordering_fields = ['created_date', 'likes_count']

    def get_queryset(self):
        return get_annotated_posts(self.request.user)

    def get_throttles(self):
        """
        GET requests use default global throttle.
        POST requests use stricter PostCreateRateThrottle.
        """
        if self.request.method == 'POST':
            return [PostCreateRateThrottle()]
        return super().get_throttles()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET for anyone; PUT/PATCH/DELETE only for the post's author."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        return get_annotated_posts(self.request.user)


class UserPostsListView(generics.ListAPIView):
    """Public timeline of one specific username."""
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    search_fields = ['content']
    ordering_fields = ['created_date', 'likes_count']
    
    def get_queryset(self):
        profile = get_object_or_404(Profile, username=self.kwargs['username'])
        return get_annotated_posts(self.request.user).filter(author=profile.user)


class FeedView(generics.ListAPIView):
    """Authenticated user's home feed: own posts + posts from followed users."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    search_fields = ['content']
    ordering_fields = ['created_date', 'likes_count']

    def get_queryset(self):
        following_ids = Follow.objects.filter(
            follower=self.request.user
        ).values_list('following_id', flat=True)
        return get_annotated_posts(self.request.user).filter(
            author_id__in=list(following_ids) + [self.request.user.id]
        )


class LikeToggleView(APIView):
    """POST to like, POST again to unlike"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [LikeRateThrottle]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()
            return Response({'is_liked': False}, status=status.HTTP_200_OK)

        return Response({'is_liked': True}, status=status.HTTP_201_CREATED)


class BookmarkToggleView(APIView):
    """POST to bookmark, POST again to remove bookmark."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            post=post
        )

        if not created:
            bookmark.delete()
            return Response({'is_bookmarked': False}, status=status.HTTP_200_OK)

        return Response({'is_bookmarked': True}, status=status.HTTP_201_CREATED)


class BookmarkListView(generics.ListAPIView):
    """List all posts bookmarked by the authenticated user."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    search_fields = ['content']
    ordering_fields = ['created_date', 'likes_count']

    def get_queryset(self):
        bookmarked_post_ids = Bookmark.objects.filter(
            user=self.request.user
        ).values_list('post_id', flat=True)
        return get_annotated_posts(self.request.user).filter(
            id__in=bookmarked_post_ids
        )
