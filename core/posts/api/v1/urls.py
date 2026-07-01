from django.urls import path
from .views import PostListCreateView, PostDetailView, UserPostsListView, FeedView


urlpatterns = [
    path('', PostListCreateView.as_view(), name='post-list-create'),
    path('feed/', FeedView.as_view(), name='post-feed'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('users/<str:username>/', UserPostsListView.as_view(), name='user-posts'),
]
