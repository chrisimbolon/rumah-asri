"""
RumahAsri — Authentication Admin
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    # ── List view ─────────────────────────────────────────────
    list_display   = ["email", "full_name", "role", "is_active", "created_at"]
    list_filter    = ["role", "is_active", "is_staff"]
    search_fields  = ["email", "full_name", "phone"]
    ordering       = ["-created_at"]

    # ── Detail view ───────────────────────────────────────────
    fieldsets = (
        (None, {
            "fields": ("email", "password")
        }),
        (_("Informasi Pribadi"), {
            "fields": ("full_name", "phone", "role", "developer")
        }),
        (_("Hak Akses"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        (_("Tanggal Penting"), {
            "fields": ("last_login", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ── Add user view ─────────────────────────────────────────
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("email", "full_name", "phone", "role", "password1", "password2"),
        }),
    )

    readonly_fields = ["created_at", "updated_at", "last_login"]
