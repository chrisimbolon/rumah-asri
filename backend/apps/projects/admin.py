"""
DevelopIndo — Projects Admin
"""
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display    = ["name", "location", "stage", "total_units", "start_date", "end_date"]
    list_filter     = ["stage", "organization"]
    search_fields   = ["name", "location"]
    ordering        = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        (None, {
            "fields": ("id", "organization", "name", "location", "description", "stage")
        }),
        ("Perencanaan", {
            "fields": ("total_units", "target_budget", "start_date", "end_date", "master_plan_url", "site_plan_url")
        }),
        ("Perizinan", {
            "fields": (
                "ipr_status", "ipr_date",
                "amdal_status", "amdal_date",
                "pbg_status", "pbg_date",
            )
        }),
        ("Sistem", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )