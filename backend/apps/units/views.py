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
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import Booking, Unit
from .serializers import (
    BookingCancelSerializer,
    BookingCreateSerializer,
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

        # Create booking
        booking = Booking.objects.create(
            unit           = unit,
            buyer          = buyer,
            organization   = org,
            spr_number     = spr_number,
            booking_fee    = data["booking_fee"],
            booking_date   = data["booking_date"],
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
    model = Unit  # for tenant scoping base

    def post(self, request, booking_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify booking belongs to this tenant
        try:
            booking = Booking.objects.select_related("unit", "buyer").get(
                id=booking_id,
                organization__in=request.user.memberships.filter(
                    is_active=True
                ).values_list("organization_id", flat=True)
                if request.user.role != "super_admin"
                else Booking.objects.values_list("organization_id", flat=True),
            )
        except Booking.DoesNotExist:
            return Response(
                {"success": False, "message": "Booking tidak ditemukan"},
                status=status.HTTP_404_NOT_FOUND,
            )

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
