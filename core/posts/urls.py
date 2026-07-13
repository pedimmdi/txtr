# posts/urls.py  (template URLs)
from django.urls import path
from posts import views

urlpatterns = [
    path('feed/', views.feed_view, name='feed'),
    # post-detail, post-create, bookmarks و بقیه — در template های بعدی اضافه میشن
]
