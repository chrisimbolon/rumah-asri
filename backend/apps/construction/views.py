"""
backend/apps/construction/views.py
DevelopIndo — Construction Views
"""
from apps.core.views import TenantScopedAPIView
from apps.units.models import Unit
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import ConstructionPhase
from .serializers import (ConstructionPhaseSerializer,
                          ConstructionPhaseUpdateSerializer,
                          ConstructionPhotoSerializer)


class PhaseListView(TenantScopedAPIView):
    """GET/POST /api/construction/<unit_id>/phases/ — developer/agent dashboard only."""
    model = Unit

    def get(self, request, unit_id):
        unit = self.get_object(unit_id)
        phases = unit.phases.all().order_by("phase_order")
        serializer = ConstructionPhaseSerializer(phases, many=True)
        return Response({
            "success":     True,
            "unit_id":     str(unit.id),
            "unit_number": unit.unit_number,
            "progress":    unit.progress,
            "phases":      serializer.data,
        })

    def post(self, request, unit_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        unit = self.get_object(unit_id)
        serializer = ConstructionPhaseSerializer(data=request.data)
        if serializer.is_valid():
            phase = serializer.save(unit=unit, updated_by=request.user)
            return Response({
                "success": True,
                "message": "Fase konstruksi berhasil dibuat",
                "phase":   ConstructionPhaseSerializer(phase).data,
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PhaseDetailView(TenantScopedAPIView):
    """PUT /api/construction/phases/<phase_id>/"""
    model = ConstructionPhase

    def put(self, request, phase_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        phase = self.get_object(phase_id)
        serializer = ConstructionPhaseUpdateSerializer(phase, data=request.data, partial=True)
        if serializer.is_valid():
            phase = serializer.save(updated_by=request.user)

            unit  = phase.unit
            total = unit.phases.count()
            done  = unit.phases.filter(status="selesai").count()
            if total > 0:
                unit.progress = round((done / total) * 100)
                ongoing = unit.phases.filter(status="proses").first()
                if ongoing:
                    unit.current_phase = ongoing.phase_name
                unit.save()

            return Response({
                "success": True,
                "message": "Fase berhasil diperbarui",
                "phase":   ConstructionPhaseSerializer(phase).data,
            })
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PhasePhotoView(TenantScopedAPIView):
    """POST /api/construction/phases/<phase_id>/photos/"""
    model = ConstructionPhase
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, phase_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        phase = self.get_object(phase_id)
        serializer = ConstructionPhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(phase=phase, uploaded_by=request.user)
            return Response({
                "success": True,
                "message": "Foto berhasil diunggah",
                "photo":   ConstructionPhotoSerializer(photo).data,
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)