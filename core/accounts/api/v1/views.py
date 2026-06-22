from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from accounts.permissions import AllowAny


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
