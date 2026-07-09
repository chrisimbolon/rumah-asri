"""
DevelopIndo — Payments Serializers
"""

from rest_framework import serializers

from .models import FinancialAudit, Payment


class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    unit_number    = serializers.CharField(source="unit.unit_number",   read_only=True)
    buyer_name     = serializers.CharField(source="unit.buyer.full_name", read_only=True)

    class Meta:
        model  = Payment
        fields = [
            "id", "payment_type", "due_date", "amount",
            "status", "status_display", "bank",
            "unit_number", "buyer_name",
            "paid_at", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Payment
        fields = ["unit", "payment_type", "due_date", "amount", "status", "bank"]

    def validate_unit(self, unit):
        user = self.context["request"].user
        if user.role == "super_admin":
            return unit
        org_ids = user.memberships.filter(is_active=True).values_list(
            "organization_id", flat=True
        )
        if unit.organization_id not in org_ids:
            raise serializers.ValidationError("Anda tidak memiliki akses ke unit ini.")
        return unit


# =============================================================================
# Sprint 27: FinancialAudit read serializer.
# =============================================================================

class FinancialAuditSerializer(serializers.ModelSerializer):
    action_display  = serializers.CharField(source="get_action_display", read_only=True)
    changed_by_name  = serializers.SerializerMethodField()
    unit_number      = serializers.CharField(source="unit.unit_number",       read_only=True, default=None)
    payment_type     = serializers.CharField(source="payment.payment_type",   read_only=True, default=None)
    booking_spr      = serializers.CharField(source="booking.spr_number",     read_only=True, default=None)

    class Meta:
        model  = FinancialAudit
        fields = [
            "id", "action", "action_display",
            "old_value", "new_value", "notes",
            "ar_before", "ar_after",
            "changed_by_name", "changed_at",
            "unit_number", "payment_type", "booking_spr",
        ]
        read_only_fields = fields

    def get_changed_by_name(self, obj):
        # None means system-triggered (mark_overdue_payments /
        # expire_bookings) — say so plainly rather than showing a
        # blank field, which would read as a bug, not a fact.
        return obj.changed_by.full_name if obj.changed_by else "Sistem (Otomatis)"