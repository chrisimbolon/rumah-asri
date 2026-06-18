"""
backend/apps/documents/views.py
RumahAsri — Documents Views
"""
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import Document
from .serializers import DocumentCreateSerializer, DocumentSerializer


class DocumentListView(TenantScopedAPIView):
    model = Document

    def get(self, request):
        documents = self.get_queryset()
        serializer = DocumentSerializer(documents, many=True, context={"request": request})
        return Response({
            "success": True,
            "count":   documents.count(),
            "results": serializer.data,
        })

    def post(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = DocumentCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            document = serializer.save(uploaded_by=request.user)
            return Response({
                "success":  True,
                "message":  "Dokumen berhasil diunggah",
                "document": DocumentSerializer(document, context={"request": request}).data,
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)