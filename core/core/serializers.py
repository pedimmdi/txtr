from rest_framework import serializers


class ToggleStateSerializer(serializers.Serializer):
    """Simple response shape used by like / follow / bookmark / repost toggles."""
    is_liked = serializers.BooleanField(required=False)
    is_following = serializers.BooleanField(required=False)
    is_bookmarked = serializers.BooleanField(required=False)
    is_reposted = serializers.BooleanField(required=False)
    is_read = serializers.BooleanField(required=False)
    status = serializers.CharField(required=False)
