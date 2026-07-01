from django.urls import path
from .views import postsview


urlpatterns = [
    path('', postsview.as_view(), name='posts'),
]