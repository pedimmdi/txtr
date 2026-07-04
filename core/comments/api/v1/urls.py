from django.urls import path
from .views import (
    CommentListCreateView,
    CommentDetailView,
    ReplyListCreateView,
    CommentLikeToggleView,
)


urlpatterns = [
    path('', CommentListCreateView.as_view(), name='comment-list-create'),
    path('<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('<int:pk>/replies/', ReplyListCreateView.as_view(), name='reply-list-create'),
    path('<int:pk>/like/', CommentLikeToggleView.as_view(), name='comment-like-toggle'),
]
