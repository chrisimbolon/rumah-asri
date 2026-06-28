# =============================================================================
# === backend/apps/projects/views.py ===
# Sprint 6: snapshot_risk() called after every requirement change
# All original views preserved — additive only.
# =============================================================================
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import (
    Project,
    ProjectRequirementStatus,
    RequirementAudit,
    RequirementEvidence,
    StageRequirement,
)
from .serializers import (
    ProjectAdvanceSerializer,
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
    RequirementEvidenceSerializer,
)


class ProjectListView(TenantScopedAPIView):
    model = Project

    def get(self, request):
        projects = self.get_queryset()
        stage = request.query_params.get("stage")
        if stage:
            projects = projects.filter(stage=stage)
        serializer = ProjectSerializer(projects, many=True)
        return Response({"success": True, "count": projects.count(), "results": serializer.data})

    def post(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response({"success": False, "message": "Tidak memiliki izin"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            project = serializer.save()
            project._create_stage_requirements()
            return Response({
                "success": True,
                "message": f"Proyek '{project.name}' berhasil dibuat",
                "project": ProjectSerializer(project).data,
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ProjectDetailView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        return Response({"success": True, "project": ProjectSerializer(project).data})

    def put(self, request, pk):
        project = self.get_object(pk)
        serializer = ProjectUpdateSerializer(project, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            project.snapshot_readiness()
            project.snapshot_risk()   # Sprint 6: risk may change after project update
            return Response({"success": True, "message": "Proyek berhasil diperbarui", "project": ProjectSerializer(project).data})
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        project = self.get_object(pk)
        if project.stage != Project.Stage.DRAFT:
            return Response({"success": False, "message": f"Proyek hanya dapat dihapus saat masih dalam tahap Draft. Tahap saat ini: {project.stage_display}."}, status=status.HTTP_400_BAD_REQUEST)
        name = project.name
        project.delete()
        return Response({"success": True, "message": f"Proyek '{name}' berhasil dihapus"})


class ProjectAdvanceView(TenantScopedAPIView):
    model = Project

    def post(self, request, pk):
        if request.user.role not in ("developer", "super_admin"):
            return Response({"success": False, "message": "Tidak memiliki izin"}, status=status.HTTP_403_FORBIDDEN)
        project = self.get_object(pk)
        serializer = ProjectAdvanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_stage = project.advance_stage()
            project.snapshot_risk()   # Sprint 6: risk changes on stage advance
            return Response({"success": True, "message": f"Proyek berhasil dilanjutkan ke tahap {project.stage_display}", "new_stage": new_stage, "project": ProjectSerializer(project).data})
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProjectIntelligenceView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        return Response({"success": True, "project_id": str(project.id), "project_name": project.name, "stage": project.stage, "stage_display": project.stage_display, "intelligence": project.get_intelligence_summary()})


class ProjectRequirementUpdateView(TenantScopedAPIView):
    """Sprint 6: snapshot_risk() called after every requirement update."""
    model = Project

    def put(self, request, pk, req_status_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response({"success": False, "message": "Tidak memiliki izin"}, status=status.HTTP_403_FORBIDDEN)
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        notes      = request.data.get("notes", req_status.notes)

        valid_statuses = [s[0] for s in ProjectRequirementStatus.Status.choices]
        if new_status not in valid_statuses:
            return Response({"success": False, "message": f"Status tidak valid. Pilihan: {valid_statuses}"}, status=status.HTTP_400_BAD_REQUEST)

        old_status = req_status.status
        project.snapshot_readiness()

        try:
            if new_status == ProjectRequirementStatus.Status.COMPLETED:
                req_status.mark_completed(user=request.user)
            else:
                req_status.status     = new_status
                req_status.notes      = notes
                req_status.updated_by = request.user
                req_status.save(update_fields=["status", "notes", "updated_by", "updated_at"])
                RequirementAudit.log(
                    requirement_status=req_status,
                    action=RequirementAudit.Action.UPDATED,
                    changed_by=request.user,
                    old_value=old_status,
                    new_value=new_status,
                    notes=notes,
                )
        except ValueError as e:
            return Response({
                "success": False,
                "message": str(e),
                "error_type": "dependency_blocked",
            }, status=status.HTTP_400_BAD_REQUEST)

        project.snapshot_risk()   # Sprint 6: risk may change after requirement update

        return Response({
            "success":      True,
            "message":      f"Requirement '{req_status.requirement.name}' diperbarui",
            "intelligence": project.get_intelligence_summary(),
        })


class ProjectPortfolioView(TenantScopedAPIView):
    model = Project

    def get(self, request):
        projects = self.get_queryset().order_by("stage", "-created_at")
        rows = []
        for p in projects:
            rows.append({
                "id": str(p.id), "name": p.name, "location": p.location,
                "stage": p.stage, "stage_display": p.stage_display,
                "readiness_score": p.readiness_score, "blocking_count": p.blocking_count,
                "next_action": p.next_action, "risk_level": p.risk_level,
                "risk_level_display": p.risk_level_display,
                "risk_score": p.risk_score,   # Sprint 6: numeric score in portfolio
                "trend": p.trend,
                "overall_progress": p.overall_progress, "total_units": p.total_units,
                "units_sold": p.units_sold,
            })
        return Response({"success": True, "count": len(rows), "results": rows})


class RequirementEvidenceView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk, req_status_id):
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        evidence = req_status.evidence.all().order_by("-uploaded_at")
        serializer = RequirementEvidenceSerializer(evidence, many=True)
        return Response({"success": True, "requirement_name": req_status.requirement.name, "requirement_status": req_status.status, "count": evidence.count(), "results": serializer.data})

    def post(self, request, pk, req_status_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response({"success": False, "message": "Tidak memiliki izin"}, status=status.HTTP_403_FORBIDDEN)
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        uploaded_file = request.FILES.get("file")
        file_url      = request.data.get("file_url", "").strip()
        notes         = request.data.get("notes", "").strip()
        if not uploaded_file and not file_url:
            return Response({"success": False, "message": "Upload file atau berikan URL bukti"}, status=status.HTTP_400_BAD_REQUEST)
        evidence = RequirementEvidence.objects.create(
            requirement_status=req_status,
            file=uploaded_file,
            file_name=uploaded_file.name if uploaded_file else "",
            file_url=file_url,
            notes=notes,
            uploaded_by=request.user,
            verification_status=RequirementEvidence.VerificationStatus.PENDING,
        )
        try:
            if req_status.status not in (
                ProjectRequirementStatus.Status.COMPLETED,
                ProjectRequirementStatus.Status.AWAITING_VERIFICATION,
            ):
                req_status.mark_awaiting_verification(user=request.user)
        except ValueError as e:
            evidence.delete()
            return Response({"success": False, "message": str(e), "error_type": "dependency_blocked"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "success":      True,
            "message":      f"Bukti untuk '{req_status.requirement.name}' berhasil diunggah",
            "evidence":     RequirementEvidenceSerializer(evidence).data,
            "intelligence": project.get_intelligence_summary(),
        }, status=status.HTTP_201_CREATED)


class RequirementEvidenceVerifyView(TenantScopedAPIView):
    model = Project

    def put(self, request, pk, req_status_id, ev_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response({"success": False, "message": "Tidak memiliki izin"}, status=status.HTTP_403_FORBIDDEN)
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        try:
            evidence = RequirementEvidence.objects.get(id=ev_id, requirement_status=req_status)
        except RequirementEvidence.DoesNotExist:
            return Response({"success": False, "message": "Bukti tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        action = request.data.get("action", "").strip()
        notes  = request.data.get("notes", "").strip()
        if action not in ("approve", "reject"):
            return Response({"success": False, "message": "Action tidak valid. Pilihan: 'approve' atau 'reject'"}, status=status.HTTP_400_BAD_REQUEST)
        if evidence.verification_status == RequirementEvidence.VerificationStatus.APPROVED:
            return Response({"success": False, "message": "Bukti ini sudah disetujui sebelumnya"}, status=status.HTTP_400_BAD_REQUEST)
        project.snapshot_readiness()
        try:
            if action == "approve":
                evidence.approve(verifier_user=request.user, notes=notes)
                message = f"Bukti disetujui — requirement '{req_status.requirement.name}' selesai"
            else:
                evidence.reject(verifier_user=request.user, notes=notes)
                message = "Bukti ditolak — developer perlu mengunggah ulang"
        except ValueError as e:
            return Response({"success": False, "message": str(e), "error_type": "dependency_blocked"}, status=status.HTTP_400_BAD_REQUEST)

        project.snapshot_risk()   # Sprint 6: risk may change after evidence approval

        return Response({"success": True, "message": message, "evidence": RequirementEvidenceSerializer(evidence).data, "intelligence": project.get_intelligence_summary()})


class ProjectActivityView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        limit = min(int(request.query_params.get("limit", 20)), 100)
        activities = project.activity_timeline(limit=limit)
        return Response({"success": True, "project_id": str(project.id), "project_name": project.name, "count": len(activities), "results": activities})


class ProjectFinancialView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        snapshot = project.financial_snapshot()
        return Response({"success": True, "project_id": str(project.id), "project_name": project.name, "financial": snapshot})
