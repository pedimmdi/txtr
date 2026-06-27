from django.urls import path
from .views import UserRegisterView, UserProfileView, UserlogoutView, PublicProfileView, CustomUserLoginView


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', CustomUserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='my-profile'),
    path('users/<str:username>/', PublicProfileView.as_view(), name='public-profile'),
    path('logout/', UserlogoutView.as_view(), name='logout'),
]
