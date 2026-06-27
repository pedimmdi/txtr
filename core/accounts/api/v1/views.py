from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import ProfileSerializer, UserSerializer, PublicProfileSerializer, CustomTokenObtainPairSerializer
from accounts.models import Profile


class UserRegisterView(APIView):
    """
    View to register a new user.
    """
    serializer_class = UserSerializer
    # Only guest users can register. Logged-in users are blocked to prevent duplicate accounts.
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    """
    View to retrieve and update the profile of the authenticated user.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    def get(self, request):
        profile = request.user.profile
        serializer = self.serializer_class(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def put(self, request):
        profile = request.user.profile
        serializer = self.serializer_class(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicProfileView(APIView):
    """
    View for viewing other users' profiles by username
    """
    permission_classes = [AllowAny]
    def get(self, request, username):
        profile = get_object_or_404(Profile, username=username)
        serializer = PublicProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomUserLoginView(TokenObtainPairView):
    """
    Custom login view that returns user information along with tokens
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserlogoutView(APIView):
    """
    View to log out a user.
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(status=205)

