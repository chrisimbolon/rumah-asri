"""
RumahAsri — Construction Views

Endpoints:
  GET  /api/construction/<unit_id>/phases/         ← get all phases for unit
  POST /api/construction/<unit_id>/phases/         ← create phase (dev only)
  PUT  /api/construction/phases/<phase_id>/        ← update phase status
  POST /api/construction/phases/<phase_id>/photos/ ← upload photo
"""

from apps.units.models import Unit
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConstructionPhase, ConstructionPhoto
from .serializers import (ConstructionPhaseSerializer,
                          ConstructionPhaseUpdateSerializer,
                          ConstructionPhotoSerializer)


def get_unit(unit_id, user):
    """Helper — get unit and check access"""
    try:
        unit = Unit.objects.get(pk=unit_id)
        if user.role == "buyer" and unit.buyer != user:
            return None, "Tidak memiliki akses ke unit ini"
        if user.role == "developer" and unit.project.developer != user:
            return None, "Tidak memiliki akses ke unit ini"
        return unit, None
    except Unit.DoesNotExist:
        return None, "Unit tidak ditemukan"


class PhaseListView(APIView):
    """GET /api/construction/<unit_id>/phases/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, unit_id):
        unit, error = get_unit(unit_id, request.user)
        if error:
            return Response(
                {"success": False, "message": error},
                status=status.HTTP_404_NOT_FOUND,
            )

        phases = unit.phases.all().order_by("phase_order")
        serializer = ConstructionPhaseSerializer(phases, many=True)
        return Response({
            "success":  True,
            "unit_id":  str(unit.id),
            "unit_number": unit.unit_number,
            "progress": unit.progress,
            "phases":   serializer.data,
        })

    def post(self, request, unit_id):
        if request.user.role not in ["developer", "super_admin"]:
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        unit, error = get_unit(unit_id, request.user)
        if error:
            return Response(
                {"success": False, "message": error},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ConstructionPhaseSerializer(data=request.data)
        if serializer.is_valid():
            phase = serializer.save(unit=unit, updated_by=request.user)
            return Response(
                {
                    "success": True,
                    "message": "Fase konstruksi berhasil dibuat",
                    "phase":   ConstructionPhaseSerializer(phase).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PhaseDetailView(APIView):
    """PUT /api/construction/phases/<phase_id>/"""
    permission_classes = [IsAuthenticated]

    def put(self, request, phase_id):
        if request.user.role not in ["developer", "super_admin"]:
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            phase = ConstructionPhase.objects.get(pk=phase_id)
        except ConstructionPhase.DoesNotExist:
            return Response(
                {"success": False, "message": "Fase tidak ditemukan"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ConstructionPhaseUpdateSerializer(
            phase, data=request.data, partial=True
        )
        if serializer.is_valid():
            phase = serializer.save(updated_by=request.user)

            # Auto-update unit progress based on completed phases
            unit   = phase.unit
            total  = unit.phases.count()
            done   = unit.phases.filter(status="selesai").count()
            if total > 0:
                unit.progress = round((done / total) * 100)
                # Update current phase
                ongoing = unit.phases.filter(status="proses").first()
                if ongoing:
                    unit.current_phase = ongoing.phase_name
                unit.save()

            return Response({
                "success": True,
                "message": "Fase berhasil diperbarui",
                "phase":   ConstructionPhaseSerializer(phase).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PhasePhotoView(APIView):
    """POST /api/construction/phases/<phase_id>/photos/"""
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request, phase_id):
        if request.user.role not in ["developer", "super_admin"]:
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            phase = ConstructionPhase.objects.get(pk=phase_id)
        except ConstructionPhase.DoesNotExist:
            return Response(
                {"success": False, "message": "Fase tidak ditemukan"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ConstructionPhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(phase=phase, uploaded_by=request.user)
            return Response(
                {
                    "success": True,
                    "message": "Foto berhasil diunggah",
                    "photo":   ConstructionPhotoSerializer(photo).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )