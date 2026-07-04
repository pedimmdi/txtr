from django.urls import path
from .views import HashtagListView, HashtagPostsView


urlpatterns = [
    path('', HashtagListView.as_view(), name='hashtag-list'),
    path('<str:name>/posts/', HashtagPostsView.as_view(), name='hashtag-posts'),
]
