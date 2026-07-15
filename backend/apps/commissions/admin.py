from django.contrib import admin

from .models import Commission, CommissionPolicy


@admin.register(CommissionPolicy)
class CommissionPolicyAdmin(admin.ModelAdmin):
    list_display = ("organization", "rate_type", "rate_value", "is_active", "updated_at")
    list_filter  = ("rate_type", "is_active")


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display  = ("agent", "booking", "amount", "status", "computed_at")
    list_filter   = ("status", "organization")
    search_fields = ("agent__full_name", "booking__spr_number")
