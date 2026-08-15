from django.urls import path
from posts import views

urlpatterns = [
    path('feed/', views.feed_view, name='feed'),
    path('explore/', views.explore_view, name='explore'),
    path('bookmarks/', views.bookmarks_view, name='bookmarks'),
    path('posts/<int:pk>/', views.post_detail_view, name='post-detail'),
    path('posts/<int:pk>/edit/', views.post_edit_view, name='post-edit'),
    path('hashtags/<str:name>/posts/', views.hashtag_posts_view, name='hashtag-posts'),
]
