"""
DevelopIndo — Units Admin
"""

from django.contrib import admin
from .models import Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display   = ["unit_number", "unit_type", "project", "buyer", "status", "progress"]
    list_filter    = ["status", "project", "unit_type"]
    search_fields  = ["unit_number", "buyer__full_name", "buyer__email"]
    ordering       = ["project", "unit_number"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("id", "project", "unit_number", "unit_type", "status")
        }),
        ("Detail Fisik & Harga", {
            "fields": ("land_area", "building_area", "price")
        }),
        ("Pembeli & Pembayaran", {
            "fields": ("buyer", "payment_method", "bank")
        }),
        ("Konstruksi", {
            "fields": ("progress", "current_phase", "target_completion")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
