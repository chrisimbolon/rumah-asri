"""
RumahAsri — Projects Admin
"""

from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display   = ["name", "location", "status", "total_units", "start_date", "end_date"]
    list_filter    = ["status", "developer"]
    search_fields  = ["name", "location"]
    ordering       = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("id", "developer", "name", "location", "description", "status")
        }),
        ("Detail Unit", {
            "fields": ("total_units",)
        }),
        ("Tanggal", {
            "fields": ("start_date", "end_date", "created_at", "updated_at")
        }),
    )
