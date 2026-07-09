# =============================================================================
# === apps/payments/views.py ===
# =============================================================================
"""
DevelopIndo — Payments Views

THE FIX for the worst bug in the codebase: the old PaymentDetailView had
zero ownership check on get() or put() — any authenticated user could
read or rewrite any payment by UUID. TenantScopedAPIView.get_object()
makes that structurally impossible now: there is no `Payment.objects.get(pk=)`
call left anywhere in this file.
"""
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import FinancialAudit, Payment
from .serializers import FinancialAuditSerializer, PaymentCreateSerializer, PaymentSerializer


class PaymentListView(TenantScopedAPIView):
    model = Payment

    def get(self, request):
        payments = self.get_queryset()

        pmt_status = request.query_params.get("status")
        if pmt_status:
            payments = payments.filter(status=pmt_status)

        serializer = PaymentSerializer(payments, many=True)
        return Response({
            "success": True,
            "count":   payments.count(),
            "results": serializer.data,
        })

    def post(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = PaymentCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            payment = serializer.save()

            # Sprint 27: ar_before computed mathematically rather than by
            # re-querying the unit pre-save (I haven't verified this
            # serializer's internal field names, so avoiding an assumption
            # there). ar_outstanding = price - sum(paid payments); this
            # payment either landed as PAID (reduced AR by its amount) or
            # didn't (no AR impact yet) — either way the "before" state is
            # exactly derivable from the "after" state plus this one fact.
            ar_after  = payment.unit.ar_outstanding
            ar_before = ar_after + payment.amount if payment.status == Payment.Status.PAID else ar_after

            FinancialAudit.log(
                organization = payment.organization,
                action       = FinancialAudit.Action.PAYMENT_RECORDED,
                changed_by   = request.user,
                payment      = payment,
                unit         = payment.unit,
                new_value    = f"Rp {payment.amount:,} ({payment.get_status_display()})",
                notes        = f"{payment.payment_type} — jatuh tempo {payment.due_date}",
                ar_before    = ar_before,
                ar_after     = ar_after,
            )

            return Response({
                "success": True,
                "message": "Pembayaran berhasil ditambahkan",
                "payment": PaymentSerializer(payment).data,
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(TenantScopedAPIView):
    model = Payment

    def get(self, request, pk):
        payment = self.get_object(pk)
        return Response({"success": True, "payment": PaymentSerializer(payment).data})

    def put(self, request, pk):
        payment = self.get_object(pk)
        old_status = payment.status
        ar_before  = payment.unit.ar_outstanding

        serializer = PaymentCreateSerializer(
            payment, data=request.data, partial=True, context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()

            # Sprint 27: only log when the status actually moved — a PUTthat edits notes/bank/etc without touching status isn't a
            # financial state change, same "only log real transitions"
            # discipline RequirementAudit already follows.
            if payment.status != old_status:
                FinancialAudit.log(
                    organization = payment.organization,
                    action       = FinancialAudit.Action.PAYMENT_STATUS_CHANGED,
                    changed_by   = request.user,
                    payment      = payment,
                    unit         = payment.unit,
                    old_value    = old_status,
                    new_value    = payment.status,
                    ar_before    = ar_before,
                    ar_after     = payment.unit.ar_outstanding,
                )

            return Response({
                "success": True,
                "message": "Pembayaran berhasil diperbarui",
                "payment": PaymentSerializer(payment).data,
            })
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# Sprint 27: read-only audit log view.
# =============================================================================

class FinancialAuditListView(TenantScopedAPIView):
    """
    GET /api/payments/audit/
    Read-only. FinancialAudit rows are never created directly through
    this API — only ever via FinancialAudit.log() from the real actions
    that trigger them (payment/booking views, the two cron commands).
    Tenant-scoped the same way every other list view here is —
    self.get_queryset() already filters to the requesting user's
    organization via TenantScopedAPIView, same super_admin bypass
    included.
    """
    model = FinancialAudit

    def get(self, request):
        entries = self.get_queryset().select_related(
            "changed_by", "unit", "payment", "booking",
        )

        action_filter = request.query_params.get("action")
        if action_filter:
            entries = entries.filter(action=action_filter)

        unit_id = request.query_params.get("unit")
        if unit_id:
            entries = entries.filter(unit__id=unit_id)

        serializer = FinancialAuditSerializer(entries, many=True)
        return Response({
            "success": True,
            "count":   entries.count(),
            "results": serializer.data,
        })
