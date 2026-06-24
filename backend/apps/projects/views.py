# =============================================================================
# === backend/apps/projects/views.py ===
# =============================================================================
"""
DevelopIndo — Projects Views + Intelligence Engine

Endpoints:
  GET  /api/projects/                    ← list with intelligence summary
  POST /api/projects/                    ← create (DRAFT stage)
  GET  /api/projects/<id>/               ← detail with full intelligence
  PUT  /api/projects/<id>/               ← update fields
  DEL  /api/projects/<id>/               ← delete (draft only)
  POST /api/projects/<id>/advance/       ← advance lifecycle stage
  GET  /api/projects/<id>/intelligence/  ← full intelligence data
  PUT  /api/projects/<id>/requirements/<req_status_id>/ ← update requirement
  GET  /api/projects/portfolio/          ← portfolio overview (intelligence table)
"""
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import Project, ProjectRequirementStatus, StageRequirement
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
            # Auto-create requirement statuses for DRAFT stage
            project._create_stage_requirements()
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
            # Snapshot readiness after update
            project.snapshot_readiness()
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
        if project.stage != Project.Stage.DRAFT:
            return Response({
                "success": False,
                "message": (
                    f"Proyek hanya dapat dihapus saat masih dalam tahap Draft. "
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
    """POST /api/projects/<id>/advance/"""
    model = Project

    def post(self, request, pk):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        project = self.get_object(pk)
        serializer = ProjectAdvanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

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


class ProjectIntelligenceView(TenantScopedAPIView):
    """
    GET /api/projects/<id>/intelligence/
    Returns full intelligence data: readiness, blocking, next action,
    risk level, trend, and all requirements with their current status.
    """
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        return Response({
            "success":      True,
            "project_id":   str(project.id),
            "project_name": project.name,
            "stage":        project.stage,
            "stage_display": project.stage_display,
            "intelligence": project.get_intelligence_summary(),
        })


class ProjectRequirementUpdateView(TenantScopedAPIView):
    """
    PUT /api/projects/<id>/requirements/<req_status_id>/
    Updates a single requirement status for a project.
    Developer marks items as in_progress, completed, or not_applicable.
    """
    model = Project

    def put(self, request, pk, req_status_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify project belongs to this tenant
        project = self.get_object(pk)

        # Get the requirement status row
        try:
            req_status = ProjectRequirementStatus.objects.get(
                id=req_status_id,
                project=project,
            )
        except ProjectRequirementStatus.DoesNotExist:
            return Response(
                {"success": False, "message": "Requirement tidak ditemukan"},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")
        notes      = request.data.get("notes", req_status.notes)

        valid_statuses = [s[0] for s in ProjectRequirementStatus.Status.choices]
        if new_status not in valid_statuses:
            return Response({
                "success": False,
                "message": f"Status tidak valid. Pilihan: {valid_statuses}",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Snapshot readiness BEFORE the change (for trend)
        project.snapshot_readiness()

        # Update
        if new_status == ProjectRequirementStatus.Status.COMPLETED:
            req_status.mark_completed(user=request.user)
        else:
            req_status.status     = new_status
            req_status.notes      = notes
            req_status.updated_by = request.user
            req_status.save(update_fields=["status", "notes", "updated_by", "updated_at"])

        # Return updated intelligence
        return Response({
            "success":      True,
            "message":      f"Requirement '{req_status.requirement.name}' diperbarui",
            "intelligence": project.get_intelligence_summary(),
        })


class ProjectPortfolioView(TenantScopedAPIView):
    """
    GET /api/projects/portfolio/
    Returns portfolio overview table — the intelligence dashboard.
    One row per project with: stage, readiness, blocking, risk, next_action, trend.
    This powers the Portfolio Dashboard the co-founder designed.
    """
    model = Project

    def get(self, request):
        projects = self.get_queryset().order_by("stage", "-created_at")

        rows = []
        for p in projects:
            rows.append({
                "id":              str(p.id),
                "name":            p.name,
                "location":        p.location,
                "stage":           p.stage,
                "stage_display":   p.stage_display,
                "readiness_score": p.readiness_score,
                "blocking_count":  p.blocking_count,
                "next_action":     p.next_action,
                "risk_level":      p.risk_level,
                "risk_level_display": p.risk_level_display,
                "trend":           p.trend,
                "overall_progress": p.overall_progress,
                "total_units":     p.total_units,
                "units_sold":      p.units_sold,
            })

        return Response({
            "success": True,
            "count":   len(rows),
            "results": rows,
        })
