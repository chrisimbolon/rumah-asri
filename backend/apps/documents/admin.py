"""
RumahAsri — Documents Admin
"""

from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display   = ["name", "doc_type", "unit", "status", "issued_date"]
    list_filter    = ["status", "doc_type", "unit__project"]
    search_fields  = ["name", "unit__unit_number", "unit__buyer__full_name"]
    ordering       = ["unit", "doc_type"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("id", "unit", "doc_type", "name", "status")
        }),
        ("File & Tanggal", {
            "fields": ("file", "issued_date", "uploaded_by")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
