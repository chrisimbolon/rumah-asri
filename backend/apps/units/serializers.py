# =============================================================================
# === backend/apps/units/serializers.py ===
# =============================================================================
"""
DevelopIndo — Units Serializers
"""
from datetime import date

from rest_framework import serializers

from apps.payments.models import FinancialAudit

from .models import Booking, Unit, UnitPriceHistory


class BookingSerializer(serializers.ModelSerializer):
    buyer_name   = serializers.CharField(source="buyer.full_name",  read_only=True)
    buyer_email  = serializers.CharField(source="buyer.email",      read_only=True)
    unit_number  = serializers.CharField(source="unit.unit_number", read_only=True)
    status_display     = serializers.CharField(source="get_status_display", read_only=True)
    kpr_status_display = serializers.CharField(source="get_kpr_status_display", read_only=True)
    is_expired   = serializers.BooleanField(read_only=True)
    is_stalled   = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Booking
        fields = [
            "id", "spr_number", "booking_fee",
            "booking_date", "expires_at", "is_expired",
            "kpr_status", "kpr_status_display", "is_stalled",
            "payment_method", "bank",
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
        request     = self.context.get("request")
        changed_by  = getattr(request, "user", None)

        # Sprint 22: log every real price change, append-only, before
        # the actual field update happens — mirrors the same "capture
        # before, then apply" order used throughout the intelligence
        # layer (readiness_before/after, etc).
        new_price = validated_data.get("price")
        if new_price is not None and new_price != instance.price:
            old_price = instance.price
            UnitPriceHistory.objects.create(
                unit=instance,
                old_price=old_price,
                new_price=new_price,
                changed_by=changed_by,
            )
            # Sprint 27: AR moves 1-for-1 with price, since ar_outstanding
            # = price - paid. Computed directly rather than via
            # instance.ar_outstanding, since instance.price hasn't been
            # updated by super().update() yet at this point.
            from apps.payments.models import Payment
            paid = sum(
                p.amount for p in instance.payments.filter(status=Payment.Status.PAID)
            )
            FinancialAudit.log(
                organization = instance.organization,
                action       = FinancialAudit.Action.PRICE_CHANGED,
                changed_by   = changed_by,
                unit         = instance,
                old_value    = f"Rp {old_price:,}",
                new_value    = f"Rp {new_price:,}",
                ar_before    = old_price - paid,
                ar_after     = new_price - paid,
            )

        # Sprint 23: when a booked unit advances to "proses" (in
        # progress), the underlying Booking has genuinely converted
        # from a pending reservation into a real sale — keep
        # Booking.status in sync so it never silently disagrees with
        # Unit.status. instance.status here is still the OLD value
        # (checked before super().update() applies the change below).
        new_status = validated_data.get("status")
        if (
            new_status == Unit.Status.IN_PROGRESS
            and instance.status == Unit.Status.BOOKED
            and hasattr(instance, "booking")
            and instance.booking.status == Booking.BookingStatus.ACTIVE
        ):
            instance.booking.status = Booking.BookingStatus.CONVERTED
            instance.booking.save(update_fields=["status", "updated_at"])

            # Sprint 27: the sale-closing moment. AR itself doesn't move
            # from this status sync alone (that's payment_recorded's
            # job) — logged as unit.ar_outstanding on both sides since
            # instance.price is still the pre-update value here, same
            # as the price-change block above.
            FinancialAudit.log(
                organization = instance.organization,
                action       = FinancialAudit.Action.BOOKING_CONVERTED,
                changed_by   = changed_by,
                booking      = instance.booking,
                unit         = instance,
                old_value    = Booking.BookingStatus.ACTIVE,
                new_value    = Booking.BookingStatus.CONVERTED,
                ar_before    = instance.ar_outstanding,
                ar_after     = instance.ar_outstanding,
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
    # Sprint 23: how many days until this booking auto-expires if
    # never converted to a real sale. Defaults to Booking.DEFAULT_EXPIRY_DAYS
    # (7) — caller can override for a longer/shorter deposit window.
    expiry_days    = serializers.IntegerField(
        required=False, min_value=1, default=7,
        help_text="Jumlah hari sebelum booking kedaluwarsa jika belum dikonversi (default 7 hari)"
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


class BookingKPRUpdateSerializer(serializers.Serializer):
    """
    PUT /api/units/bookings/<id>/kpr/
    Sprint 24: deliberately trimmed — a plain status field update, no
    transition guard. Any valid KPRStatus choice is accepted in any
    order (a rejected KPR reverting to "belum_diajukan" for reapplying
    is a completely normal real-world case, unlike Unit's lifecycle
    which genuinely has illegal jumps to prevent).
    """
    kpr_status = serializers.ChoiceField(choices=Booking.KPRStatus.choices)
