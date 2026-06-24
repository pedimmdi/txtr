from rest_framework import serializers
from accounts.models import User, Profile


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
        fields = ['user', 'first_name', 'last_name', 'image', 'bio']
        extra_kwargs = {'user': {'read_only': True}}
