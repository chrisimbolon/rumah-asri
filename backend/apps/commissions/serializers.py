# =============================================================================
# === backend/apps/commissions/serializers.py ===
# =============================================================================
from rest_framework import serializers

from .models import Commission, CommissionPolicy


class CommissionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model  = CommissionPolicy
        fields = ["id", "rate_type", "rate_value", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CommissionSerializer(serializers.ModelSerializer):
    """
    Only `status` is writable through this serializer — amount, agent,
    and booking are set once at creation (the booking hook) and never
    change afterward. A staff member can transition a commission's
    status, never edit what it's actually worth or who it's for.
    """
    agent_name     = serializers.CharField(source="agent.full_name", read_only=True)
    agent_email    = serializers.CharField(source="agent.email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    booking_spr    = serializers.CharField(source="booking.spr_number", read_only=True)
    unit_number    = serializers.CharField(source="booking.unit.unit_number", read_only=True, default=None)

    class Meta:
        model  = Commission
        fields = [
            "id", "booking", "booking_spr", "unit_number",
            "agent", "agent_name", "agent_email",
            "amount", "status", "status_display",
            "computed_at", "updated_at",
        ]
        read_only_fields = [
            "id", "booking", "booking_spr", "unit_number",
            "agent", "agent_name", "agent_email",
            "amount", "computed_at", "updated_at",
        ]
