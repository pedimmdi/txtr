from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from accounts.models import Profile, Follow
from posts.models import Post
from posts.permissions import IsAuthorOrReadOnly
from .serializers import PostSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class PostListCreateView(generics.ListCreateAPIView):
    """GET: public list of all posts. POST: create a post as request.user."""
    queryset = Post.objects.select_related('author', 'author__profile').order_by('-updated_date')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET for anyone; PUT/PATCH/DELETE only for the post's author."""
    queryset = Post.objects.select_related('author', 'author__profile')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]


class UserPostsListView(generics.ListAPIView):
    """Public timeline of one specific username."""
    serializer_class = PostSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        profile = get_object_or_404(Profile, username=self.kwargs['username'])
        return Post.objects.filter(
            author=profile.user
        ).select_related('author', 'author__profile')


class FeedView(generics.ListAPIView):
    """Authenticated user's home feed: own posts + posts from followed users."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        following_ids = Follow.objects.filter(
            follower=self.request.user
        ).values_list('following_id', flat=True)
        return Post.objects.filter(
            author_id__in=list(following_ids) + [self.request.user.id]
        ).select_related('author', 'author__profile').order_by('-updated_date')
