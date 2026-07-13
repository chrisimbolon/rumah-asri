# === backend/apps/crm/admin.py ===
from django.contrib import admin

from .models import Prospect


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = (
        "name", "phone", "status", "interested_project",
        "assigned_to", "organization", "next_followup_date", "created_at",
    )
    list_filter = ("status", "organization")
    search_fields = ("name", "phone", "notes")
