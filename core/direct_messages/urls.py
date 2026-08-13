from django.urls import path
from direct_messages import views

urlpatterns = [
    path('messages/',          views.dm_list_view,         name='messages'),
    path('messages/<str:username>/', views.dm_conversation_view, name='conversation'),
]
