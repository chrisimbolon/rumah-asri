# =============================================================================
# === backend/apps/projects/views.py ===
# =============================================================================
"""
DevelopIndo — Projects Views

Endpoints:
  GET  /api/projects/           ← list all projects for org
  POST /api/projects/           ← create new project (DRAFT stage)
  GET  /api/projects/<id>/      ← get single project with full lifecycle data
  PUT  /api/projects/<id>/      ← update project fields
  DEL  /api/projects/<id>/      ← delete project (draft only)
  POST /api/projects/<id>/advance/ ← advance to next lifecycle stage
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.views import TenantScopedAPIView

from .models import Project
from .serializers import (
    ProjectAdvanceSerializer,
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
)


class ProjectListView(TenantScopedAPIView):
    model = Project

    def get(self, request):
        projects = self.get_queryset()

        # Optional filter by stage
        stage = request.query_params.get("stage")
        if stage:
            projects = projects.filter(stage=stage)

        serializer = ProjectSerializer(projects, many=True)
        return Response({
            "success": True,
            "count":   projects.count(),
            "results": serializer.data,
        })

    def post(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ProjectCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            project = serializer.save()
            return Response({
                "success": True,
                "message": f"Proyek '{project.name}' berhasil dibuat",
                "project": ProjectSerializer(project).data,
            }, status=status.HTTP_201_CREATED)
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProjectDetailView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        return Response({
            "success": True,
            "project": ProjectSerializer(project).data,
        })

    def put(self, request, pk):
        project = self.get_object(pk)
        serializer = ProjectUpdateSerializer(
            project, data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Proyek berhasil diperbarui",
                "project": ProjectSerializer(project).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        project = self.get_object(pk)
        # Only allow deletion if project is still in DRAFT
        if project.stage != Project.Stage.DRAFT:
            return Response({
                "success": False,
                "message": (
                    "Proyek hanya dapat dihapus saat masih dalam tahap Draft. "
                    f"Tahap saat ini: {project.stage_display}."
                ),
            }, status=status.HTTP_400_BAD_REQUEST)
        name = project.name
        project.delete()
        return Response({
            "success": True,
            "message": f"Proyek '{name}' berhasil dihapus",
        })


class ProjectAdvanceView(TenantScopedAPIView):
    """
    POST /api/projects/<id>/advance/
    Advance the project to the next lifecycle stage.
    Enforces all blocking rules (e.g. PBG must be approved before konstruksi).
    """
    model = Project

    def post(self, request, pk):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        project = self.get_object(pk)

        # Validate confirmation
        serializer = ProjectAdvanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Attempt stage advancement
        try:
            new_stage = project.advance_stage()
            return Response({
                "success":   True,
                "message":   f"Proyek berhasil dilanjutkan ke tahap {project.stage_display}",
                "new_stage": new_stage,
                "project":   ProjectSerializer(project).data,
            })
        except ValueError as e:
            return Response({
                "success": False,
                "message": str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
