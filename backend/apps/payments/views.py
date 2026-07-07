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

from .models import Payment
from .serializers import PaymentCreateSerializer, PaymentSerializer


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
        serializer = PaymentCreateSerializer(
            payment, data=request.data, partial=True, context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Pembayaran berhasil diperbarui",
                "payment": PaymentSerializer(payment).data,
            })
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
