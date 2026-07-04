from django.urls import path
from .views import (
    PostListCreateView, PostDetailView,
    UserPostsListView, FeedView, LikeToggleView,
    BookmarkToggleView, BookmarkListView,
)


urlpatterns = [
    path('', PostListCreateView.as_view(), name='post-list-create'),
    path('feed/', FeedView.as_view(), name='post-feed'),
    path('bookmarks/', BookmarkListView.as_view(), name='bookmark-list'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('<int:pk>/like/', LikeToggleView.as_view(), name='post-like-toggle'),
    path('<int:pk>/bookmark/', BookmarkToggleView.as_view(), name='post-bookmark-toggle'),
    path('users/<str:username>/', UserPostsListView.as_view(), name='user-posts'),
]
