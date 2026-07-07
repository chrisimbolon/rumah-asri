# =============================================================================
# === backend/apps/units/views.py ===
# =============================================================================
"""
DevelopIndo — Units Views

Endpoints:
  GET  /api/units/              ← list all units for org
  POST /api/units/              ← create new unit
  GET  /api/units/<id>/         ← get single unit
  PUT  /api/units/<id>/         ← update unit
  POST /api/units/<id>/book/    ← book a unit (pre-sale)
  POST /api/bookings/<id>/cancel/ ← cancel a booking
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import Booking, Unit
from .serializers import (
    BookingCancelSerializer,
    BookingCreateSerializer,
    BookingKPRUpdateSerializer,
    BookingSerializer,
    UnitCreateSerializer,
    UnitSerializer,
)


class UnitListView(TenantScopedAPIView):
    model = Unit

    def get(self, request):
        units = self.get_queryset()

        project_id  = request.query_params.get("project")
        unit_status = request.query_params.get("status")

        if project_id:
            units = units.filter(project__id=project_id)
        if unit_status:
            units = units.filter(status=unit_status)

        serializer = UnitSerializer(units, many=True)
        return Response({
            "success": True,
            "count":   units.count(),
            "results": serializer.data,
        })

    def post(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = UnitCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            unit = serializer.save()
            return Response({
                "success": True,
                "message": f"Unit {unit.unit_number} berhasil dibuat",
                "unit":    UnitSerializer(unit).data,
            }, status=status.HTTP_201_CREATED)
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UnitDetailView(TenantScopedAPIView):
    model = Unit

    def get(self, request, pk):
        unit = self.get_object(pk)
        return Response({"success": True, "unit": UnitSerializer(unit).data})

    def put(self, request, pk):
        unit = self.get_object(pk)
        serializer = UnitCreateSerializer(
            unit, data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": f"Unit {unit.unit_number} berhasil diperbarui",
                "unit":    UnitSerializer(unit).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UnitBookingView(TenantScopedAPIView):
    """
    POST /api/units/<id>/book/
    Books an available unit — the core pre-sales transaction.

    What happens:
      1. Validates unit is "tersedia"
      2. Creates Booking record with auto-generated SPR number
      3. Sets unit.status = "dipesan"
      4. Sets unit.buyer = the booking buyer
      5. Returns full unit + booking data
    """
    model = Unit

    def post(self, request, pk):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        unit = self.get_object(pk)

        # Only available units can be booked
        if unit.status != Unit.Status.AVAILABLE:
            return Response({
                "success": False,
                "message": (
                    f"Unit {unit.unit_number} tidak dapat dipesan. "
                    f"Status saat ini: {unit.get_status_display()}."
                ),
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = BookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data  = serializer.validated_data
        buyer = data["buyer_id"]  # already resolved to CustomUser in validate_buyer_id

        # Get organization from unit
        org = unit.organization

        # Generate SPR number
        spr_number = Booking.generate_spr_number(org)

        # Sprint 23: compute the deposit-window deadline. Measured from
        # NOW (not booking_date), since that's when the clock on "pay
        # up or lose the reservation" actually starts ticking.
        expiry_days = data.get("expiry_days", Booking.DEFAULT_EXPIRY_DAYS)
        expires_at  = timezone.now() + timedelta(days=expiry_days)

        # Create booking
        booking = Booking.objects.create(
            unit           = unit,
            buyer          = buyer,
            organization   = org,
            spr_number     = spr_number,
            booking_fee    = data["booking_fee"],
            booking_date   = data["booking_date"],
            expires_at     = expires_at,
            payment_method = data.get("payment_method", ""),
            bank           = data.get("bank", ""),
            notes          = data.get("notes", ""),
            created_by     = request.user,
        )

        # Update unit status and buyer
        unit.status = Unit.Status.BOOKED
        unit.buyer  = buyer
        unit.save(update_fields=["status", "buyer", "updated_at"])

        return Response({
            "success": True,
            "message": (
                f"Unit {unit.unit_number} berhasil dipesan oleh {buyer.full_name}. "
                f"SPR: {spr_number}"
            ),
            "booking": {
                "id":            str(booking.id),
                "spr_number":    booking.spr_number,
                "booking_fee":   booking.booking_fee,
                "booking_date":  str(booking.booking_date),
                "expires_at":    booking.expires_at.isoformat() if booking.expires_at else None,
                "payment_method": booking.payment_method,
                "bank":          booking.bank,
                "buyer_name":    buyer.full_name,
                "buyer_email":   buyer.email,
            },
            "unit": UnitSerializer(unit).data,
        }, status=status.HTTP_201_CREATED)


class BookingCancelView(TenantScopedAPIView):
    """
    POST /api/bookings/<id>/cancel/
    Cancels an active booking — restores unit to "tersedia".
    """
    # Sprint 24: now scoped to Booking directly, using the standard
    # self.get_object() pattern — the hand-rolled inline tenant query
    # that used to live here is gone, replaced by Booking's new
    # for_user() manager (see BookingQuerySet in models.py). Same
    # pattern every other tenant-scoped view in this codebase already
    # uses; this one just hadn't caught up yet.
    model = Booking

    def post(self, request, booking_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        booking = self.get_object(booking_id)

        if booking.status != Booking.BookingStatus.ACTIVE:
            return Response({
                "success": False,
                "message": f"Booking sudah {booking.get_status_display()}.",
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = BookingCancelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cancel booking
        booking.status        = Booking.BookingStatus.CANCELLED
        booking.cancelled_at  = timezone.now()
        booking.cancelled_by  = request.user
        booking.cancel_reason = serializer.validated_data.get("reason", "")
        booking.save()

        # Restore unit to available
        unit        = booking.unit
        unit.status = Unit.Status.AVAILABLE
        unit.buyer  = None
        unit.save(update_fields=["status", "buyer", "updated_at"])

        return Response({
            "success": True,
            "message": f"Booking {booking.spr_number} berhasil dibatalkan. Unit {unit.unit_number} kembali tersedia.",
            "unit":    UnitSerializer(unit).data,
        })


class BookingKPRUpdateView(TenantScopedAPIView):
    """
    PUT /api/units/bookings/<id>/kpr/
    Sprint 24: updates a booking's KPR financing status. Deliberately
    trimmed — a plain status field update, no transition guard (see
    BookingKPRUpdateSerializer's docstring for why). Just enough for
    a developer to track "where is this sale's financing at," and for
    Booking.is_stalled to have something real to compute against.
    """
    model = Booking

    def put(self, request, booking_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        booking = self.get_object(booking_id)

        serializer = BookingKPRUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.kpr_status = serializer.validated_data["kpr_status"]
        booking.save(update_fields=["kpr_status", "updated_at"])

        return Response({
            "success": True,
            "message": f"Status KPR {booking.spr_number} diperbarui menjadi {booking.get_kpr_status_display()}.",
            "booking": BookingSerializer(booking).data,
        })
