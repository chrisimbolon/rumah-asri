"""
RumahAsri — Payments Serializers
"""

from rest_framework import serializers

from .models import Payment


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