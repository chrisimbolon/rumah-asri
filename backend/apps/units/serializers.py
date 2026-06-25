# =============================================================================
# === backend/apps/units/serializers.py ===
# =============================================================================
"""
DevelopIndo — Units Serializers
"""
from datetime import date

from rest_framework import serializers

from .models import Booking, Unit


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


class UnitSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    project_name   = serializers.CharField(source="project.name",       read_only=True)
    buyer_name     = serializers.CharField(source="buyer.full_name",    read_only=True)
    buyer_email    = serializers.CharField(source="buyer.email",        read_only=True)
    booking        = BookingSerializer(read_only=True)

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
            "booking",
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
