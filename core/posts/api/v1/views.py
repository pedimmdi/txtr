from django.db.models import Count, Exists, OuterRef
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
)
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from accounts.models import Profile, Follow
from posts.models import Post, Like, Bookmark
from posts.permissions import IsAuthorOrReadOnly
from core.throttles import PostCreateRateThrottle, LikeRateThrottle
from .serializers import PostSerializer
from core.pagination import StandardResultsSetPagination
from core.serializers import ToggleStateSerializer


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


@extend_schema_view(
    get=extend_schema(
        tags=['Posts'],
        summary='List all posts',
        description='Public paginated list of posts. Supports ?search= and ?ordering=.',
    ),
    post=extend_schema(
        tags=['Posts'],
        summary='Create a new post',
        description='Create a text-only post (max 1000 characters). Requires authentication.',
        request=PostSerializer,
        responses={201: PostSerializer},
    ),
)
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
        if self.request.method == 'POST':
            return [PostCreateRateThrottle()]
        return super().get_throttles()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@extend_schema_view(
    get=extend_schema(tags=['Posts'], summary='Retrieve a post'),
    put=extend_schema(tags=['Posts'], summary='Update a post (author only)'),
    patch=extend_schema(tags=['Posts'], summary='Partial update a post (author only)'),
    delete=extend_schema(tags=['Posts'], summary='Delete a post (author only)'),
)
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET for anyone; PUT/PATCH/DELETE only for the post's author."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        return get_annotated_posts(self.request.user)


@extend_schema_view(
    get=extend_schema(
        tags=['Posts'],
        summary='List posts by username',
        description='Public timeline of a specific user.',
    )
)
class UserPostsListView(generics.ListAPIView):
    """Public timeline of one specific username."""
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    search_fields = ['content']
    ordering_fields = ['created_date', 'likes_count']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Post.objects.none()
        profile = get_object_or_404(Profile, username=self.kwargs['username'])
        return get_annotated_posts(self.request.user).filter(author=profile.user)


@extend_schema_view(
    get=extend_schema(
        tags=['Posts'],
        summary='Home feed',
        description='Authenticated user\'s feed: own posts + posts from followed users.',
    )
)
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
    serializer_class = ToggleStateSerializer

    @extend_schema(
        tags=['Posts'],
        summary='Like / Unlike a post',
        description='Toggle like on a post. Returns the new state.',
        responses={
            201: OpenApiResponse(description='Liked', examples=[
                OpenApiExample('Liked', value={'is_liked': True}),
            ]),
            200: OpenApiResponse(description='Unliked', examples=[
                OpenApiExample('Unliked', value={'is_liked': False}),
            ]),
        },
    )
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
    serializer_class = ToggleStateSerializer

    @extend_schema(
        tags=['Posts'],
        summary='Bookmark / Unbookmark a post',
        description='Toggle bookmark on a post.',
        responses={
            201: OpenApiResponse(description='Bookmarked', examples=[
                OpenApiExample('Bookmarked', value={'is_bookmarked': True}),
            ]),
            200: OpenApiResponse(description='Removed', examples=[
                OpenApiExample('Removed', value={'is_bookmarked': False}),
            ]),
        },
    )
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


@extend_schema_view(
    get=extend_schema(
        tags=['Posts'],
        summary='List my bookmarked posts',
        description='Paginated list of posts bookmarked by the authenticated user.',
    )
)
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
    serializer_class = ToggleStateSerializer

    @extend_schema(
        tags=['Posts'],
        summary='Repost / Undo repost',
        description='Toggle pure repost of an original post. Cannot repost your own post or a repost.',
        responses={
            201: OpenApiResponse(description='Reposted', examples=[
                OpenApiExample('Reposted', value={'is_reposted': True}),
            ]),
            200: OpenApiResponse(description='Undo', examples=[
                OpenApiExample('Undo', value={'is_reposted': False}),
            ]),
            400: OpenApiResponse(description='Cannot repost own post or invalid target'),
        },
    )
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

    @extend_schema(
        tags=['Posts'],
        summary='Quote repost',
        description='Create a quote repost (new post with content that references an original post).',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'content': {'type': 'string', 'description': 'Your quote text (required)'},
                },
                'required': ['content'],
            }
        },
        responses={
            201: PostSerializer,
            400: OpenApiResponse(description='Content is required'),
        },
    )
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
