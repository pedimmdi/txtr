from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source='sender.profile.username',
        read_only=True
    )
    sender_image = serializers.ImageField(
        source='sender.profile.image',
        read_only=True
    )
    message = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'sender_username', 'sender_image',
            'notification_type', 'message',
            'post', 'comment',
            'is_read', 'created_at'
        ]

    def get_message(self, obj):
        username = obj.sender.profile.username
        messages = {
            Notification.NotificationType.LIKE:
                f"{username} liked your post",
            Notification.NotificationType.COMMENT:
                f"{username} commented on your post",
            Notification.NotificationType.REPLY:
                f"{username} replied to your comment",
            Notification.NotificationType.COMMENT_LIKE:
                f"{username} liked your comment",
            Notification.NotificationType.FOLLOW:
                f"{username} started following you",
            Notification.NotificationType.REPOST:
                f"{username} reposted your post",
            Notification.NotificationType.MENTION:
                f"{username} mentioned you",
            Notification.NotificationType.DIRECT_MESSAGE:
                f"{username} sent you a message",
        }
        return messages.get(obj.notification_type, '')
