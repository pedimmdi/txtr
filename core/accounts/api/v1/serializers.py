from rest_framework import serializers
from accounts.models import User, Profile, Follow
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']
        """
        The password field should be write-only
        to ensure that it is not included in the serialized output when retrieving user data. 
        This is a security measure to prevent exposing sensitive information.
        """
        extra_kwargs = {'password': {'write_only': True}}
        
        def create(self, validated_data):
            """
            Override the create method to handle password hashing.
            """
            user = User(
                email=validated_data['email'],
            ) 
            user.set_password(validated_data['password'])
            user.save()
            return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user', 'username', 'birth_date', 'image', 'bio']
        extra_kwargs = {'user': {'read_only': True}}


class PublicProfileSerializer(serializers.ModelSerializer):
    """A serializer for displaying users' public profiles."""
    is_following = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['username', 'image', 'bio', 'birth_date',
                  'is_following', 'followers_count', 'following_count']

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(follower=request.user, following=obj.user).exists()

    def get_followers_count(self, obj):
        return obj.user.followers.count()

    def get_following_count(self, obj):
        return obj.user.following.count()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # login and getting tokens
        data = super().validate(attrs)
        user = self.user
        profile = getattr(user, 'profile', None)
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'username': profile.username if profile else None,
            'image': profile.image.url if profile and profile.image else None,
            'bio': profile.bio if profile else "",
        }
        return data
