"""
RumahAsri — Authentication Views

Endpoints:
  POST /api/auth/register/   ← create new account
  POST /api/auth/login/      ← get access + refresh tokens
  POST /api/auth/refresh/    ← refresh access token
  POST /api/auth/logout/     ← blacklist refresh token
  GET  /api/auth/me/         ← get current user profile
  PUT  /api/auth/me/         ← update current user profile
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import (LoginSerializer, RegisterSerializer,
                          TokenResponseSerializer, UserSerializer)


# ── Register ──────────────────────────────────────────────────
class RegisterView(APIView):
    """
    POST /api/auth/register/
    Create a new Developer or Buyer account.
    Returns JWT tokens immediately after registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user   = serializer.save()
        tokens = TokenResponseSerializer.get_tokens(user)

        return Response(
            {
                "success": True,
                "message": f"Selamat datang, {user.full_name}! Akun berhasil dibuat.",
                **tokens,
            },
            status=status.HTTP_201_CREATED,
        )


# ── Login ─────────────────────────────────────────────────────
class LoginView(APIView):
    """
    POST /api/auth/login/
    Authenticate with email + password.
    Returns access token, refresh token, and user data.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user   = serializer.validated_data["user"]
        tokens = TokenResponseSerializer.get_tokens(user)

        return Response(
            {
                "success": True,
                "message": f"Selamat datang kembali, {user.full_name}!",
                **tokens,
            },
            status=status.HTTP_200_OK,
        )


# ── Refresh ───────────────────────────────────────────────────
class RefreshView(APIView):
    """
    POST /api/auth/refresh/
    Exchange a refresh token for a new access token.
    Body: { "refresh": "<refresh_token>" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token wajib diisi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            return Response(
                {
                    "success": True,
                    "access":  str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        except TokenError as e:
            return Response(
                {"success": False, "message": "Token tidak valid atau sudah expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


# ── Logout ────────────────────────────────────────────────────
class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklist the refresh token — user can no longer refresh.
    Body: { "refresh": "<refresh_token>" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token wajib diisi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"success": True, "message": "Logout berhasil"},
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                {"success": False, "message": "Token tidak valid"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ── Me ────────────────────────────────────────────────────────
class MeView(APIView):
    """
    GET  /api/auth/me/  ← get current user
    PUT  /api/auth/me/  ← update current user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(
            {"success": True, "user": serializer.data},
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(
            {"success": True, "user": serializer.data},
            status=status.HTTP_200_OK,
        )
