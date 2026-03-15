"""
RumahAsri — Custom User Model
Email-based authentication with role field
"""

import uuid

from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser — uses email instead of username"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email wajib diisi")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff",     True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role",         CustomUser.Role.SUPER_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser harus is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser harus is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for RumahAsri.
    Uses email as the unique identifier instead of username.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        DEVELOPER   = "developer",   "Developer / Admin"
        AGENT       = "agent",       "Agen Penjualan"
        BUYER       = "buyer",       "Pembeli"

    # ── Core fields ───────────────────────────────────────────
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email      = models.EmailField(unique=True, verbose_name="Alamat Email")
    full_name  = models.CharField(max_length=150, verbose_name="Nama Lengkap")
    phone      = models.CharField(max_length=20, blank=True, verbose_name="Nomor Telepon")
    role       = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.BUYER,
        verbose_name="Peran",
    )

    # ── Developer relation (null for buyers/agents) ───────────
    developer  = models.ForeignKey(
        "self",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="team_members",
        verbose_name="Developer",
        help_text="Hanya untuk agen & admin yang terhubung ke developer",
    )

    # ── Status ────────────────────────────────────────────────
    is_active  = models.BooleanField(default=True,  verbose_name="Aktif")
    is_staff   = models.BooleanField(default=False, verbose_name="Staff")

    # ── Timestamps ────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Manager ───────────────────────────────────────────────
    objects = CustomUserManager()

    # ── Auth config ───────────────────────────────────────────
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name        = "Pengguna"
        verbose_name_plural = "Pengguna"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.email}) — {self.get_role_display()}"

    # ── Role helpers ──────────────────────────────────────────
    @property
    def is_developer(self):
        return self.role == self.Role.DEVELOPER

    @property
    def is_buyer(self):
        return self.role == self.Role.BUYER

    @property
    def is_agent(self):
        return self.role == self.Role.AGENT

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN
