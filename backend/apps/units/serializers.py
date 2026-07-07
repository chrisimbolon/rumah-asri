# =============================================================================
# === backend/apps/units/serializers.py ===
# =============================================================================
"""
DevelopIndo — Units Serializers
"""
from datetime import date

from rest_framework import serializers

from .models import Booking, Unit, UnitPriceHistory


class BookingSerializer(serializers.ModelSerializer):
    buyer_name   = serializers.CharField(source="buyer.full_name",  read_only=True)
    buyer_email  = serializers.CharField(source="buyer.email",      read_only=True)
    unit_number  = serializers.CharField(source="unit.unit_number", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model  = Booking
        fields = [
            "id", "spr_number", "booking_fee",
            "booking_date", "payment_method", "bank",
            "status", "status_display", "notes",
            "buyer", "buyer_name", "buyer_email",
            "unit_number", "created_at",
        ]
        read_only_fields = ["id", "spr_number", "created_at"]


class UnitPriceHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.full_name", read_only=True)

    class Meta:
        model  = UnitPriceHistory
        fields = ["id", "old_price", "new_price", "changed_by_name", "changed_at"]
        read_only_fields = fields


class UnitSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    project_name   = serializers.CharField(source="project.name",       read_only=True)
    buyer_name     = serializers.CharField(source="buyer.full_name",    read_only=True)
    buyer_email    = serializers.CharField(source="buyer.email",        read_only=True)
    booking        = BookingSerializer(read_only=True)
    price_history  = UnitPriceHistorySerializer(many=True, read_only=True)

    class Meta:
        model  = Unit
        fields = [
            "id", "unit_number", "unit_type",
            "land_area", "building_area", "price",
            "status", "status_display",
            "progress", "current_phase", "target_completion",
            "payment_method", "bank",
            "project", "project_name",
            "buyer", "buyer_name", "buyer_email",
            "booking", "price_history",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UnitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Unit
        fields = [
            "project", "unit_number", "unit_type",
            "land_area", "building_area", "price",
            "status", "progress", "current_phase",
            "target_completion", "payment_method", "bank",
            "buyer",
        ]

    def validate_project(self, project):
        user = self.context["request"].user
        if user.role == "super_admin":
            return project
        org_ids = user.memberships.filter(is_active=True).values_list(
            "organization_id", flat=True
        )
        if project.organization_id not in org_ids:
            raise serializers.ValidationError(
                "Anda tidak memiliki akses ke proyek ini."
            )
        return project

    def validate(self, attrs):
        # Sprint 22: status transition guard. Only applies on UPDATE
        # (self.instance exists) — a fresh Unit being created has no
        # "current" status to violate, it just starts wherever the
        # model default says (tersedia).
        if self.instance is not None and "status" in attrs:
            new_status = attrs["status"]
            if new_status != self.instance.status:
                can_transition, reason = self.instance.can_transition_to(new_status)
                if not can_transition:
                    raise serializers.ValidationError({"status": reason})
        return attrs

    def update(self, instance, validated_data):
        # Sprint 22: log every real price change, append-only, before
        # the actual field update happens — mirrors the same "capture
        # before, then apply" order used throughout the intelligence
        # layer (readiness_before/after, etc).
        new_price = validated_data.get("price")
        if new_price is not None and new_price != instance.price:
            request = self.context.get("request")
            UnitPriceHistory.objects.create(
                unit=instance,
                old_price=instance.price,
                new_price=new_price,
                changed_by=getattr(request, "user", None),
            )
        return super().update(instance, validated_data)


class BookingCreateSerializer(serializers.Serializer):
    """
    POST /api/units/<id>/book/
    Records a booking for an available unit.
    """
    buyer_id       = serializers.UUIDField(
        help_text="UUID of the buyer (CustomUser with role=buyer)"
    )
    booking_fee    = serializers.IntegerField(
        min_value=1,
        help_text="Booking fee amount in IDR"
    )
    booking_date   = serializers.DateField(
        default=date.today,
        help_text="Date of booking (defaults to today)"
    )
    payment_method = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    bank           = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    notes          = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    def validate_buyer_id(self, value):
        from apps.authentication.models import CustomUser
        try:
            buyer = CustomUser.objects.get(id=value, role="buyer")
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                "Pembeli tidak ditemukan atau bukan akun buyer."
            )
        return buyer


class BookingCancelSerializer(serializers.Serializer):
    """POST /api/bookings/<id>/cancel/"""
    reason = serializers.CharField(
        required=False, allow_blank=True, default="",
        help_text="Alasan pembatalan (opsional)"
    )
