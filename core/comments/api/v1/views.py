from django.db.models import Count, Exists, OuterRef
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, IsAuthenticated
)
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from posts.models import Post
from comments.models import Comment, CommentLike
from comments.permissions import IsAuthorOrReadOnly
from .serializers import CommentSerializer
from core.throttles import CommentCreateRateThrottle, LikeRateThrottle
from core.pagination import StandardResultsSetPagination
from core.serializers import ToggleStateSerializer


def get_annotated_comments(user):
    """
    Returns a Comment queryset annotated with likes_count, is_liked, replies_count.
    distinct=True prevents double-counting when multiple JOINs are involved.
    Explicit order_by keeps pagination deterministic.
    """
    qs = Comment.objects.select_related('author', 'author__profile').annotate(
        likes_count=Count('comment_likes', distinct=True),
        replies_count=Count('replies', distinct=True),
    )
    if user and user.is_authenticated:
        user_likes = CommentLike.objects.filter(comment=OuterRef('pk'), user=user)
        qs = qs.annotate(is_liked=Exists(user_likes))
    return qs.order_by('created_date', 'id')


@extend_schema_view(
    get=extend_schema(
        tags=['Comments'],
        summary='List top-level comments of a post',
        description='Paginated list of top-level comments (parent=None) for the given post.',
    ),
    post=extend_schema(
        tags=['Comments'],
        summary='Create a comment on a post',
        description='Create a new top-level comment. Requires authentication.',
        request=CommentSerializer,
        responses={201: CommentSerializer},
    ),
)
class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET: top-level comments for a post (parent=None).
    POST: create a new comment on the post.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    search_fields = ['content']
    ordering_fields = ['created_date', 'likes_count']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        return get_annotated_comments(self.request.user).filter(
            post=post,
            parent=None
        )

    def get_throttles(self):
        if self.request.method == 'POST':
            return [CommentCreateRateThrottle()]
        return super().get_throttles()

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)


@extend_schema_view(
    get=extend_schema(tags=['Comments'], summary='Retrieve a comment'),
    put=extend_schema(tags=['Comments'], summary='Update a comment (author only)'),
    patch=extend_schema(tags=['Comments'], summary='Partial update a comment (author only)'),
    delete=extend_schema(tags=['Comments'], summary='Delete a comment (author only)'),
)
class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET for anyone; PUT/PATCH/DELETE only for the comment's author."""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()
        return get_annotated_comments(self.request.user).filter(
            post_id=self.kwargs['post_pk']
        )


@extend_schema_view(
    get=extend_schema(
        tags=['Comments'],
        summary='List replies to a comment',
        description='Paginated list of replies to a top-level comment.',
    ),
    post=extend_schema(
        tags=['Comments'],
        summary='Reply to a comment',
        description='Create a reply. Only allowed on top-level comments (one level of nesting).',
        request=CommentSerializer,
        responses={201: CommentSerializer},
    ),
)
class ReplyListCreateView(generics.ListCreateAPIView):
    """
    GET: replies for a specific comment.
    POST: create a reply. Only allowed on top-level comments (parent=None).
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()
        parent = get_object_or_404(
            Comment,
            pk=self.kwargs['pk'],
            post_id=self.kwargs['post_pk'],
            parent=None
        )
        return get_annotated_comments(self.request.user).filter(parent=parent)

    def get_throttles(self):
        if self.request.method == 'POST':
            return [CommentCreateRateThrottle()]
        return super().get_throttles()

    def perform_create(self, serializer):
        parent = get_object_or_404(
            Comment,
            pk=self.kwargs['pk'],
            post_id=self.kwargs['post_pk'],
            parent=None
        )
        serializer.save(
            author=self.request.user,
            post=parent.post,
            parent=parent
        )


class CommentLikeToggleView(APIView):
    """POST to like, POST again to unlike."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [LikeRateThrottle]
    serializer_class = ToggleStateSerializer

    @extend_schema(
        tags=['Comments'],
        summary='Like / Unlike a comment',
        description='Toggle like on a comment. Returns the new state.',
        responses={
            201: OpenApiResponse(description='Liked', examples=[
                OpenApiExample('Liked', value={'is_liked': True}),
            ]),
            200: OpenApiResponse(description='Unliked', examples=[
                OpenApiExample('Unliked', value={'is_liked': False}),
            ]),
        },
    )
    def post(self, request, post_pk, pk):
        comment = get_object_or_404(Comment, pk=pk, post_id=post_pk)
        like, created = CommentLike.objects.get_or_create(
            user=request.user,
            comment=comment
        )

        if not created:
            like.delete()
            return Response({'is_liked': False}, status=status.HTTP_200_OK)

        return Response({'is_liked': True}, status=status.HTTP_201_CREATED)
