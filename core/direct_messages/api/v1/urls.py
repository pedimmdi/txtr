from django.urls import path
from .views import ConversationListView, ConversationDetailView, MessageDeleteView


urlpatterns = [
    path('', ConversationListView.as_view(), name='conversation-list'),
    path('<str:username>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('<str:username>/<int:pk>/', MessageDeleteView.as_view(), name='message-delete'),
]
