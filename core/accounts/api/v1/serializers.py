from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models import User, Profile, Follow


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    class Meta:
        model = User
        fields = ['email', 'password']
        # The password field is write-only so it's never included
        # in serialized output when retrieving user data.
        extra_kwargs = {'password': {'write_only': True}}
        
    def create(self, validated_data):
        """
        Override create to ensure the password is hashed via set_password,
        instead of being saved as plain text.
        """
        user = User(email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the authenticated user's email and/or password.
    """
    password = serializers.CharField(
        write_only=True, required=False, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ['email', 'password']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


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
