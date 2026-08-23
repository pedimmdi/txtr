from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from accounts.models import Profile, Follow
from accounts.permissions import OnlyAnonymousUsers
from .serializers import (
    ProfileSerializer, UserSerializer, UserUpdateSerializer,
    PublicProfileSerializer, CustomTokenObtainPairSerializer
)
from core.throttles import AuthRateThrottle, FollowRateThrottle
from core.pagination import StandardResultsSetPagination
from core.serializers import ToggleStateSerializer


class UserRegisterView(APIView):
    """
    View to register a new user.
    """
    throttle_classes = [AuthRateThrottle]
    serializer_class = UserSerializer
    permission_classes = [OnlyAnonymousUsers]

    @extend_schema(
        tags=['Auth'],
        summary='Register a new user',
        description='Create a new account with email and password. Only available to anonymous users.',
        request=UserSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer, description='User created successfully'),
            400: OpenApiResponse(description='Validation error'),
        },
    )
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

    @extend_schema(
        tags=['Accounts'],
        summary='Get my profile',
        description='Retrieve the profile of the currently authenticated user.',
        responses={200: ProfileSerializer},
    )
    def get(self, request):
        profile = request.user.profile
        serializer = self.serializer_class(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Accounts'],
        summary='Update my profile',
        description='Update username, bio, image or birth_date of the authenticated user.',
        request=ProfileSerializer,
        responses={200: ProfileSerializer},
    )
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

    @extend_schema(
        tags=['Accounts'],
        summary='Update email or password',
        description='Update the authenticated user\'s email and/or password.',
        request=UserUpdateSerializer,
        responses={200: UserUpdateSerializer},
    )
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

    @extend_schema(
        tags=['Accounts'],
        summary='Get public profile by username',
        description='Retrieve a public profile including follower/following counts and is_following status.',
        responses={200: PublicProfileSerializer, 404: OpenApiResponse(description='User not found')},
    )
    def get(self, request, username):
        profile = get_object_or_404(Profile, username=username)
        serializer = PublicProfileSerializer(profile, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomUserLoginView(TokenObtainPairView):
    """
    Custom login view that returns user information along with tokens
    """
    throttle_classes = [AuthRateThrottle]
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        tags=['Auth'],
        summary='Login (JWT)',
        description='Obtain access and refresh tokens. Also returns basic user profile data.',
        responses={200: OpenApiResponse(description='Tokens + user data')},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserLogoutView(APIView):
    """
    Blacklist the refresh token to log the user out of the API.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        summary='Logout (blacklist refresh token)',
        description='Blacklist the provided refresh token so it can no longer be used.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string', 'description': 'Refresh token to blacklist'},
                },
                'required': ['refresh'],
            }
        },
        responses={
            205: OpenApiResponse(description='Successfully logged out'),
            400: OpenApiResponse(description='Missing or invalid refresh token'),
        },
    )
    def post(self, request):
        refresh_token = request.data.get('refresh') or request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Invalid or expired refresh token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class FollowToggleView(APIView):
    """
    Follow or unfollow a user by username. Same request toggles the state.
    """
    throttle_classes = [FollowRateThrottle]
    permission_classes = [IsAuthenticated]
    serializer_class = ToggleStateSerializer

    @extend_schema(
        tags=['Social'],
        summary='Follow / Unfollow a user',
        description='Toggle follow status for the given username. Returns the new state.',
        responses={
            201: OpenApiResponse(description='Now following', examples=[
                OpenApiExample('Following', value={'is_following': True}),
            ]),
            200: OpenApiResponse(description='Unfollowed', examples=[
                OpenApiExample('Not following', value={'is_following': False}),
            ]),
            400: OpenApiResponse(description='Cannot follow yourself'),
        },
    )
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


@extend_schema_view(
    get=extend_schema(
        tags=['Social'],
        summary='List followers of a user',
        description='Paginated list of users who follow the given username.',
    )
)
class FollowersListView(generics.ListAPIView):
    """
    List of users who follow the given username.
    """
    serializer_class = PublicProfileSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Profile.objects.none()
        profile = get_object_or_404(Profile, username=self.kwargs['username'])
        follower_ids = profile.user.followers.values_list('follower_id', flat=True)
        return Profile.objects.filter(user_id__in=follower_ids).order_by('username')

    def get_serializer_context(self):
        return {'request': self.request}


@extend_schema_view(
    get=extend_schema(
        tags=['Social'],
        summary='List users that a user is following',
        description='Paginated list of users that the given username follows.',
    )
)
class FollowingListView(generics.ListAPIView):
    """
    List of users that the given username follows.
    """
    serializer_class = PublicProfileSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Profile.objects.none()
        profile = get_object_or_404(Profile, username=self.kwargs['username'])
        following_ids = profile.user.following.values_list('following_id', flat=True)
        return Profile.objects.filter(user_id__in=following_ids).order_by('username')

    def get_serializer_context(self):
        return {'request': self.request}


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts'],
        summary='Search users',
        description='Search public profiles by username (supports ?search= and pagination).',
    )
)
class UserSearchView(generics.ListAPIView):
    """Search users by username."""
    serializer_class = PublicProfileSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    search_fields = ['username']

    def get_queryset(self):
        return Profile.objects.select_related('user').all()

    def get_serializer_context(self):
        return {'request': self.request}
