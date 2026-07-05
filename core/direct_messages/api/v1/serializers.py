from rest_framework import serializers
from accounts.models import Profile
from direct_messages.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source='sender.profile.username',
        read_only=True
    )
    sender_image = serializers.ImageField(
        source='sender.profile.image',
        read_only=True
    )

    class Meta:
        model = Message
        fields = [
            'id', 'sender_username', 'sender_image',
            'content', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'sender_username', 'sender_image', 'is_read', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'other_user', 'last_message', 'unread_count', 'updated_at']

    def get_other_user(self, obj):
        """Return the other participant's basic info."""
        request = self.context.get('request')
        other = obj.participants.exclude(id=request.user.id).first()
        if not other:
            return None
        try:
            return {
                'username': other.profile.username,
                'image': request.build_absolute_uri(other.profile.image.url)
                if other.profile.image else None
            }
        except Profile.DoesNotExist:
            return None

    def get_last_message(self, obj):
        last = obj.messages.last()
        if not last:
            return None
        return {
            'content': last.content,
            'created_at': last.created_at
        }

    def get_unread_count(self, obj):
        """Count messages not sent by me and not yet read."""
        request = self.context.get('request')
        return obj.messages.filter(
            is_read=False
        ).exclude(
            sender=request.user
        ).count()
