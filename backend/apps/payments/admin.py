"""
RumahAsri — Payments Admin
"""

from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display   = ["unit", "payment_type", "amount", "due_date", "status", "bank"]
    list_filter    = ["status", "bank", "unit__project"]
    search_fields  = ["unit__unit_number", "unit__buyer__full_name"]
    ordering       = ["due_date"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("id", "unit", "payment_type", "amount", "due_date")
        }),
        ("Status & Bank", {
            "fields": ("status", "bank", "paid_at")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
