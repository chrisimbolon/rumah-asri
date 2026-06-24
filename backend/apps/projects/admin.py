# =============================================================================
# === backend/apps/projects/admin.py ===
# =============================================================================
"""
DevelopIndo — Projects Admin
"""
from django.contrib import admin

from .models import Project, ProjectRequirementStatus, StageRequirement


@admin.register(StageRequirement)
class StageRequirementAdmin(admin.ModelAdmin):
    list_display  = ["name", "stage", "is_mandatory", "order", "is_active"]
    list_filter   = ["stage", "is_mandatory", "is_active"]
    search_fields = ["name", "description"]
    ordering      = ["stage", "order"]


@admin.register(ProjectRequirementStatus)
class ProjectRequirementStatusAdmin(admin.ModelAdmin):
    list_display  = ["project", "requirement", "status", "completed_at", "updated_by"]
    list_filter   = ["status", "requirement__stage"]
    search_fields = ["project__name", "requirement__name"]
    ordering      = ["project", "requirement__order"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display    = ["name", "location", "stage", "total_units", "start_date", "end_date"]
    list_filter     = ["stage", "organization"]
    search_fields   = ["name", "location"]
    ordering        = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at",
                       "readiness_score_last", "readiness_score_updated_at"]
    fieldsets = (
        (None, {
            "fields": ("id", "organization", "name", "location", "description", "stage")
        }),
        ("Perencanaan", {
            "fields": ("total_units", "target_budget", "start_date", "end_date",
                       "master_plan_url", "site_plan_url")
        }),
        ("Perizinan", {
            "fields": ("ipr_status", "ipr_date",
                       "amdal_status", "amdal_date",
                       "pbg_status", "pbg_date")
        }),
        ("Intelligence Snapshot", {
            "fields": ("readiness_score_last", "readiness_score_updated_at"),
            "classes": ("collapse",),
        }),
        ("Sistem", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
