"""
RumahAsri — Construction Admin
"""

from django.contrib import admin
from .models import ConstructionPhase, ConstructionPhoto


class ConstructionPhotoInline(admin.TabularInline):
    model  = ConstructionPhoto
    extra  = 0
    fields = ["image", "caption", "uploaded_by", "uploaded_at"]
    readonly_fields = ["uploaded_at"]


@admin.register(ConstructionPhase)
class ConstructionPhaseAdmin(admin.ModelAdmin):
    list_display   = ["unit", "phase_order", "phase_name", "status", "phase_date"]
    list_filter    = ["status", "unit__project"]
    search_fields  = ["unit__unit_number", "phase_name"]
    ordering       = ["unit", "phase_order"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines        = [ConstructionPhotoInline]


@admin.register(ConstructionPhoto)
class ConstructionPhotoAdmin(admin.ModelAdmin):
    list_display  = ["phase", "caption", "uploaded_by", "uploaded_at"]
    list_filter   = ["phase__unit__project"]
    readonly_fields = ["id", "uploaded_at"]
