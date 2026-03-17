"""
RumahAsri — Payments Views
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import PaymentCreateSerializer, PaymentSerializer


class PaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == "super_admin":
            payments = Payment.objects.all()
        elif request.user.role == "buyer":
            payments = Payment.objects.filter(unit__buyer=request.user)
        else:
            payments = Payment.objects.filter(unit__project__developer=request.user)

        # Filter by status
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
        if request.user.role not in ["developer", "super_admin"]:
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Pembayaran berhasil ditambahkan",
                    "payment": PaymentSerializer(payment).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            return Response(
                {"success": False, "message": "Pembayaran tidak ditemukan"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            "success": True,
            "payment": PaymentSerializer(payment).data,
        })

    def put(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            return Response(
                {"success": False, "message": "Pembayaran tidak ditemukan"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PaymentCreateSerializer(payment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Pembayaran berhasil diperbarui",
                "payment": PaymentSerializer(payment).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )