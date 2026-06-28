from django.urls import path
from .views import (
    UserRegisterView, UserProfileView, UserUpdateView, UserLogoutView,
    PublicProfileView, CustomUserLoginView,
    FollowToggleView, FollowersListView, FollowingListView
)


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', CustomUserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='my-profile'),
    path('me/', UserUpdateView.as_view(), name='user-update'),
    path('users/<str:username>/', PublicProfileView.as_view(), name='public-profile'),
    path('users/<str:username>/follow/', FollowToggleView.as_view(), name='follow-toggle'),
    path('users/<str:username>/followers/', FollowersListView.as_view(), name='followers-list'),
    path('users/<str:username>/following/', FollowingListView.as_view(), name='following-list'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
