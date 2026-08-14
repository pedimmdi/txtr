from django.urls import path
from accounts import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.profile_edit_view, name='profile-edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
]
