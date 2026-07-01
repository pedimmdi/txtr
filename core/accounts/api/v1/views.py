from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from accounts.models import Profile, Follow
from accounts.permissions import OnlyAnonymousUsers
from rest_framework.pagination import PageNumberPagination
from .serializers import (
    ProfileSerializer, UserSerializer, UserUpdateSerializer,
    PublicProfileSerializer, CustomTokenObtainPairSerializer
)


class UserRegisterView(APIView):
    """
    View to register a new user.
    """
    serializer_class = UserSerializer
    # Only guest users can register. Logged-in users are blocked to prevent duplicate accounts.
    permission_classes = [OnlyAnonymousUsers]
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


class UserUpdateView(APIView):
    """
    View to update the authenticated user's email and/or password
    (separate from Profile, since email/password live on the User model).
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
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
        serializer = PublicProfileSerializer(profile, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomUserLoginView(TokenObtainPairView):
    """
    Custom login view that returns user information along with tokens
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserLogoutView(APIView):
    """
    View to log out a user.
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(status=205)


class FollowToggleView(APIView):
    """
    Follow or unfollow a user by username. Same request toggles the state.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        profile = get_object_or_404(Profile, username=username)
        target_user = profile.user

        if target_user == request.user:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )

        if not created:
            follow.delete()
            return Response({"is_following": False}, status=status.HTTP_200_OK)

        return Response({"is_following": True}, status=status.HTTP_201_CREATED)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


class FollowersListView(generics.ListAPIView):
    """
    List of users who follow the given username.
    """
    serializer_class = PublicProfileSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        profile = get_object_or_404(Profile, username=self.kwargs['username'])
        follower_ids = profile.user.followers.values_list('follower_id', flat=True)
        return Profile.objects.filter(user_id__in=follower_ids)

    def get_serializer_context(self):
        return {'request': self.request}


class FollowingListView(generics.ListAPIView):
    """
    List of users that the given username follows.
    """
    serializer_class = PublicProfileSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        profile = get_object_or_404(Profile, username=self.kwargs['username'])
        following_ids = profile.user.following.values_list('following_id', flat=True)
        return Profile.objects.filter(user_id__in=following_ids)

    def get_serializer_context(self):
        return {'request': self.request}
