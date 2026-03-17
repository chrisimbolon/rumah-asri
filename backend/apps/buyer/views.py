"""
RumahAsri — Buyer Portal Views

All buyer-facing API endpoints in one clean place.
Every buyer sees ONLY their own unit data.

Endpoints:
  GET /api/buyer/me/          ← unit + progress + buyer info
  GET /api/buyer/timeline/    ← construction phases
  GET /api/buyer/payments/    ← payment schedule & status
  GET /api/buyer/documents/   ← documents (PPJB, IMB, AJB etc)
"""

from apps.construction.models import ConstructionPhase
from apps.construction.serializers import ConstructionPhaseSerializer
from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer
from apps.units.models import Unit
from apps.units.serializers import UnitSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


# ── Helper ────────────────────────────────────────────────────
def get_buyer_unit(user):
    """
    Returns (unit, error_response) for the logged-in buyer.
    Only buyers can call this — developers and admins are blocked.
    """
    if user.role != "buyer":
        return None, Response(
            {"success": False, "message": "Endpoint ini hanya untuk pembeli"},
            status=status.HTTP_403_FORBIDDEN,
        )
    try:
        unit = Unit.objects.select_related(
            "project", "buyer"
        ).get(buyer=user)
        return unit, None
    except Unit.DoesNotExist:
        return None, Response(
            {
                "success": False,
                "message": (
                    "Unit belum ditetapkan untuk akun Anda. "
                    "Silakan hubungi developer atau agen penjualan."
                ),
            },
            status=status.HTTP_404_NOT_FOUND,
        )


# ── GET /api/buyer/me/ ────────────────────────────────────────
class BuyerMeView(APIView):
    """
    Returns the logged-in buyer's unit with full details.
    This is the main data source for the Buyer Portal homepage.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unit, error = get_buyer_unit(request.user)
        if error:
            return error

        unit_data = UnitSerializer(unit).data

        return Response({
            "success": True,
            "buyer": {
                "id":           str(request.user.id),
                "full_name":    request.user.full_name,
                "email":        request.user.email,
                "phone":        request.user.phone,
            },
            "unit": unit_data,
            "project": {
                "id":       str(unit.project.id),
                "name":     unit.project.name,
                "location": unit.project.location,
                "status":   unit.project.status,
            },
        })


# ── GET /api/buyer/timeline/ ──────────────────────────────────
class BuyerTimelineView(APIView):
    """
    Returns the construction timeline for the buyer's unit.
    7 phases from land clearing to handover.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unit, error = get_buyer_unit(request.user)
        if error:
            return error

        phases = unit.phases.all().order_by("phase_order")
        serializer = ConstructionPhaseSerializer(phases, many=True)

        done_count  = phases.filter(status="selesai").count()
        total       = phases.count()
        active_phase = phases.filter(status="proses").first()

        return Response({
            "success":      True,
            "unit_number":  unit.unit_number,
            "progress":     unit.progress,
            "done_count":   done_count,
            "total_phases": total,
            "current_phase": active_phase.phase_name if active_phase else unit.current_phase,
            "phases":       serializer.data,
        })


# ── GET /api/buyer/payments/ ──────────────────────────────────
class BuyerPaymentsView(APIView):
    """
    Returns the payment schedule and status for the buyer's unit.
    Includes KPR instalments, down payment, final payment etc.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unit, error = get_buyer_unit(request.user)
        if error:
            return error

        payments   = unit.payments.all().order_by("due_date")
        serializer = PaymentSerializer(payments, many=True)

        total_amount    = sum(p.amount for p in payments)
        paid_amount     = sum(p.amount for p in payments if p.status == "lunas")
        overdue_count   = payments.filter(status="menunggak").count()

        return Response({
            "success":        True,
            "unit_number":    unit.unit_number,
            "payment_method": unit.payment_method,
            "bank":           unit.bank,
            "total_amount":   total_amount,
            "paid_amount":    paid_amount,
            "overdue_count":  overdue_count,
            "total_count":    payments.count(),
            "payments":       serializer.data,
        })


# ── GET /api/buyer/documents/ ─────────────────────────────────
class BuyerDocumentsView(APIView):
    """
    Returns all documents for the buyer's unit.
    PPJB, IMB, AJB, invoice, handover certificate etc.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unit, error = get_buyer_unit(request.user)
        if error:
            return error

        documents  = unit.documents.all().order_by("doc_type")
        serializer = DocumentSerializer(
            documents,
            many=True,
            context={"request": request},
        )

        available_count = documents.filter(status="tersedia").count()

        return Response({
            "success":         True,
            "unit_number":     unit.unit_number,
            "total_documents": documents.count(),
            "available_count": available_count,
            "documents":       serializer.data,
        })
