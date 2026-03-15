"""
RumahAsri — Authentication Serializers
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser


# ── User serializer (safe — no password) ─────────────────────
class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model  = CustomUser
        fields = [
            "id", "email", "full_name", "phone",
            "role", "role_display", "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ── Register serializer ───────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(
        write_only=True, min_length=8,
        style={"input_type": "password"},
        error_messages={"min_length": "Kata sandi minimal 8 karakter"},
    )
    password2 = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        label="Konfirmasi kata sandi",
    )

    class Meta:
        model  = CustomUser
        fields = ["email", "full_name", "phone", "password", "password2", "role"]

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email ini sudah terdaftar")
        return value.lower()

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Kata sandi tidak cocok"})
        # Only allow developer and buyer roles on registration
        allowed_roles = [CustomUser.Role.DEVELOPER, CustomUser.Role.BUYER]
        if data.get("role") not in allowed_roles:
            raise serializers.ValidationError({"role": "Peran tidak valid untuk pendaftaran"})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user     = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ── Login serializer ──────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField(label="Email")
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        label="Kata sandi",
    )

    def validate(self, data):
        email    = data.get("email", "").lower()
        password = data.get("password", "")

        if not email or not password:
            raise serializers.ValidationError("Email dan kata sandi wajib diisi")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                "Email atau kata sandi salah. Silakan coba lagi."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "Akun Anda dinonaktifkan. Hubungi administrator."
            )

        data["user"] = user
        return data


# ── Token response serializer ─────────────────────────────────
class TokenResponseSerializer(serializers.Serializer):
    """Builds the token response payload after login"""

    @staticmethod
    def get_tokens(user):
        refresh = RefreshToken.for_user(user)
        # Add custom claims to the token payload
        refresh["email"]     = user.email
        refresh["full_name"] = user.full_name
        refresh["role"]      = user.role

        return {
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
            "user":    UserSerializer(user).data,
        }
