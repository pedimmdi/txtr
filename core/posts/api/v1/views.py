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
        'author', 'author__profile',
        'original_post', 'original_post__author', 'original_post__author__profile'
    ).prefetch_related(
        'hashtags'
    ).annotate(
        likes_count=Count('likes', distinct=True),
        reposts_count=Count('reposts', distinct=True),
    ).order_by('-created_date')
    if user and user.is_authenticated:
        user_likes = Like.objects.filter(post=OuterRef('pk'), user=user)
        user_bookmarks = Bookmark.objects.filter(post=OuterRef('pk'), user=user)
        user_reposts = Post.objects.filter(original_post=OuterRef('pk'), author=user)
        qs = qs.annotate(
            is_liked=Exists(user_likes),
            is_bookmarked=Exists(user_bookmarks),
            is_reposted=Exists(user_reposts),
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


class RepostToggleView(APIView):
    """
    POST to repost, POST again to undo the repost.
    Only original posts can be reposted (no repost of a repost).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        original_post = get_object_or_404(Post, pk=pk, original_post=None)

        if original_post.author == request.user:
            return Response(
                {'error': 'You cannot repost your own post'},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_repost = Post.objects.filter(
            author=request.user,
            original_post=original_post
        ).first()

        if existing_repost:
            existing_repost.delete()
            return Response({'is_reposted': False}, status=status.HTTP_200_OK)

        Post.objects.create(
            author=request.user,
            original_post=original_post,
            content=''
        )
        return Response({'is_reposted': True}, status=status.HTTP_201_CREATED)


class QuoteRepostView(APIView):
    """
    Repost a post with added comment (Quote Tweet style).
    A quote repost is just a new Post with content + original_post set.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        original_post = get_object_or_404(Post, pk=pk, original_post=None)
        content = request.data.get('content', '').strip()

        if not content:
            return Response(
                {'error': 'Content is required for a quote repost'},
                status=status.HTTP_400_BAD_REQUEST
            )

        post = Post.objects.create(
            author=request.user,
            original_post=original_post,
            content=content
        )
        serializer = PostSerializer(
            get_annotated_posts(request.user).get(pk=post.pk),
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
