from rest_framework import serializers
from accounts.models import Profile
from direct_messages.models import Conversation, Message
from posts.models import Post


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source='sender.profile.username',
        read_only=True
    )
    sender_image = serializers.ImageField(
        source='sender.profile.image',
        read_only=True
    )
    reply_to_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )
    reply_to = serializers.SerializerMethodField()
    forwarded_post_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )
    forwarded_post = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'sender_username',
            'sender_image',
            'content',
            'is_read',
            'created_at',
            'reply_to_id',
            'reply_to',
            'forwarded_post_id',
            'forwarded_post',
        ]
        read_only_fields = [
            'id',
            'sender_username',
            'sender_image',
            'is_read',
            'created_at',
            'reply_to',
            'forwarded_post',
        ]

    def get_reply_to(self, obj):
        if not obj.reply_to_id:
            return None
        parent = obj.reply_to
        if not parent:
            return None
        return {
            'id': parent.id,
            'content': parent.content,
            'sender_username': parent.sender.profile.username,
            'has_forwarded_post': parent.forwarded_post_id is not None,
        }

    def get_forwarded_post(self, obj):
        post = obj.forwarded_post
        if not post:
            return None
        # If this is a pure repost wrapper, show the original content
        display = post.original_post if (post.original_post_id and not post.content) else post
        author = display.author.profile
        request = self.context.get('request')
        image_url = None
        if author.image:
            image_url = (
                request.build_absolute_uri(author.image.url)
                if request else author.image.url
            )
        return {
            'id': post.id,
            'content': display.content,
            'author_username': author.username,
            'author_image': image_url,
            'url': f'/posts/{post.id}/',
        }


class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'other_user', 'last_message', 'unread_count', 'updated_at']

    def get_other_user(self, obj):
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
        content = last.content
        if not content and last.forwarded_post_id:
            content = 'Forwarded a post'
        return {
            'content': content,
            'created_at': last.created_at
        }

    def get_unread_count(self, obj):
        request = self.context.get('request')
        return obj.messages.filter(
            is_read=False
        ).exclude(
            sender=request.user
        ).count()
