from django.urls import path
from .views import UserRegisterView, UserProfileView, UserlogoutView


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('logout/', UserlogoutView.as_view(), name='logout'),
]
