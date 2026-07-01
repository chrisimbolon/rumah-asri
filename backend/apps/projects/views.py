# =============================================================================
# === backend/apps/projects/views.py ===
# Sprint 8: evidence version tracking + self-verify guard
# All Sprint 1-7 views preserved — additive only.
# =============================================================================
from datetime import date
from django.db import models as django_models
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import (
    Project,
    ProjectRequirementStatus,
    RequirementAudit,
    RequirementComment,
    RequirementEvidence,
    StageRequirement,
)
from .serializers import (
    ProjectAdvanceSerializer,
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
    RequirementCommentSerializer,
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
            return Response({"success": True, "message": f"Proyek '{project.name}' berhasil dibuat", "project": ProjectSerializer(project).data}, status=status.HTTP_201_CREATED)
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
            project.snapshot_risk()
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
            project.snapshot_risk()
            return Response({"success": True, "message": f"Proyek berhasil dilanjutkan ke tahap {project.stage_display}", "new_stage": new_stage, "project": ProjectSerializer(project).data})
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProjectIntelligenceView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        return Response({"success": True, "project_id": str(project.id), "project_name": project.name, "stage": project.stage, "stage_display": project.stage_display, "intelligence": project.get_intelligence_summary()})


class ProjectRequirementUpdateView(TenantScopedAPIView):
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
                RequirementAudit.log(requirement_status=req_status, action=RequirementAudit.Action.UPDATED, changed_by=request.user, old_value=old_status, new_value=new_status, notes=notes)
        except ValueError as e:
            return Response({"success": False, "message": str(e), "error_type": "dependency_blocked"}, status=status.HTTP_400_BAD_REQUEST)

        project.snapshot_risk()
        return Response({"success": True, "message": f"Requirement '{req_status.requirement.name}' diperbarui", "intelligence": project.get_intelligence_summary()})


class ProjectPortfolioView(TenantScopedAPIView):
    model = Project

    def get(self, request):
        projects = self.get_queryset().order_by("stage", "-created_at")
        rows = []
        for p in projects:
            rows.append({"id": str(p.id), "name": p.name, "location": p.location, "stage": p.stage, "stage_display": p.stage_display, "readiness_score": p.readiness_score, "blocking_count": p.blocking_count, "next_action": p.next_action, "risk_level": p.risk_level, "risk_level_display": p.risk_level_display, "risk_score": p.risk_score, "trend": p.trend, "overall_progress": p.overall_progress, "total_units": p.total_units, "units_sold": p.units_sold})
        return Response({"success": True, "count": len(rows), "results": rows})


class MyActionsView(TenantScopedAPIView):
    """
    Sprint 9: Personalized, prioritized next-actions feed for the
    logged-in user across ALL their organization's projects.

    GET /api/projects/my-actions/

    Returns:
      my_tasks:         [...] — requirements assigned to me, sorted by priority
      my_tasks_count:    int
      unassigned:        [...] — actionable + unassigned, sorted by priority
      unassigned_count:  int
      total_actionable:  int

    Each item includes project context, requirement details,
    priority_score, action_type, and human-readable reasons —
    everything needed to render an actionable card without
    additional API calls.

    No model field — pure computed intelligence reusing
    Sprint 4 (dependency), Sprint 5 (weight), Sprint 6 (risk),
    Sprint 7 (ownership), Sprint 8 (evidence status) data.
    """
    model = Project

    def get(self, request):
        actions = Project.get_my_actions(request.user)
        return Response({
            "success": True,
            **actions,
        })

# =============================================================================
# Sprint 7: Assign requirement + set due_date
# =============================================================================

class AssignRequirementView(TenantScopedAPIView):
    model = Project

    def put(self, request, pk, req_status_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response({"success": False, "message": "Tidak memiliki izin"}, status=status.HTTP_403_FORBIDDEN)

        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        assigned_to_id = request.data.get("assigned_to")
        due_date_str   = request.data.get("due_date")
        update_fields  = ["updated_at"]
        changed        = False

        if "assigned_to" in request.data:
            if assigned_to_id is None:
                old_name = req_status.assigned_to.full_name if req_status.assigned_to else None
                req_status.assigned_to = None
                update_fields.append("assigned_to")
                if old_name:
                    RequirementAudit.log(requirement_status=req_status, action=RequirementAudit.Action.ASSIGNED, changed_by=request.user, old_value=old_name, new_value="", notes="Penugasan dibatalkan")
                changed = True
            else:
                org_members = project.get_org_members()
                try:
                    assignee = org_members.get(id=assigned_to_id)
                except Exception:
                    return Response({"success": False, "message": "Pengguna tidak ditemukan atau bukan anggota organisasi ini"}, status=status.HTTP_400_BAD_REQUEST)
                old_name = req_status.assigned_to.full_name if req_status.assigned_to else None
                req_status.assigned_to = assignee
                update_fields.append("assigned_to")
                RequirementAudit.log(requirement_status=req_status, action=RequirementAudit.Action.ASSIGNED, changed_by=request.user, old_value=old_name or "", new_value=assignee.full_name, notes=f"Ditugaskan ke {assignee.full_name}")
                changed = True

        if "due_date" in request.data:
            if due_date_str is None:
                old_due = req_status.due_date.isoformat() if req_status.due_date else None
                req_status.due_date = None
                update_fields.append("due_date")
                if old_due:
                    RequirementAudit.log(requirement_status=req_status, action=RequirementAudit.Action.DUE_DATE_SET, changed_by=request.user, old_value=old_due, new_value="", notes="Tenggat waktu dihapus")
                changed = True
            else:
                try:
                    from datetime import datetime
                    new_due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except ValueError:
                    return Response({"success": False, "message": "Format tanggal tidak valid. Gunakan YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
                old_due = req_status.due_date.isoformat() if req_status.due_date else None
                req_status.due_date = new_due
                update_fields.append("due_date")
                RequirementAudit.log(requirement_status=req_status, action=RequirementAudit.Action.DUE_DATE_SET, changed_by=request.user, old_value=old_due or "", new_value=due_date_str, notes=f"Tenggat waktu ditetapkan: {due_date_str}")
                changed = True

        if not changed:
            return Response({"success": False, "message": "Tidak ada perubahan yang dikirim"}, status=status.HTTP_400_BAD_REQUEST)

        req_status.save(update_fields=list(set(update_fields)))
        return Response({"success": True, "message": f"Requirement '{req_status.requirement.name}' diperbarui", "intelligence": project.get_intelligence_summary()})


# =============================================================================
# Sprint 7: Requirement comments
# =============================================================================

class RequirementCommentView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk, req_status_id):
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        comments = req_status.comments.select_related("author").order_by("created_at")
        serializer = RequirementCommentSerializer(comments, many=True)
        return Response({"success": True, "requirement_name": req_status.requirement.name, "count": comments.count(), "results": serializer.data})

    def post(self, request, pk, req_status_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response({"success": False, "message": "Tidak memiliki izin"}, status=status.HTTP_403_FORBIDDEN)
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        body = request.data.get("body", "").strip()
        if not body:
            return Response({"success": False, "message": "Komentar tidak boleh kosong"}, status=status.HTTP_400_BAD_REQUEST)
        if len(body) > 2000:
            return Response({"success": False, "message": "Komentar maksimal 2000 karakter"}, status=status.HTTP_400_BAD_REQUEST)
        comment = RequirementComment.objects.create(requirement_status=req_status, author=request.user, body=body)
        RequirementAudit.log(requirement_status=req_status, action=RequirementAudit.Action.COMMENT_ADDED, changed_by=request.user, notes=body[:100] + ("..." if len(body) > 100 else ""))
        serializer = RequirementCommentSerializer(comment)
        return Response({"success": True, "message": "Komentar berhasil ditambahkan", "comment": serializer.data}, status=status.HTTP_201_CREATED)


# =============================================================================
# Sprint 7: Org members list
# =============================================================================

class ProjectOrgMembersView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        members = project.get_org_members()
        results = [{"id": str(m.id), "full_name": m.full_name, "email": m.email, "role": m.role} for m in members]
        return Response({"success": True, "count": len(results), "results": results})


# =============================================================================
# Sprint 8: Evidence upload — with version tracking
# =============================================================================

class RequirementEvidenceView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk, req_status_id):
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        evidence = req_status.evidence.all().order_by("-version_number", "-uploaded_at")
        serializer = RequirementEvidenceSerializer(evidence, many=True, context={"request": request})
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

        # ── Sprint 8: version tracking ────────────────────────
        existing_latest = req_status.evidence.filter(is_latest=True).first()
        next_version    = 1
        if existing_latest:
            max_v        = req_status.evidence.aggregate(max_v=django_models.Max("version_number"))["max_v"] or 0
            next_version = max_v + 1

        # Create new evidence
        evidence = RequirementEvidence.objects.create(
            requirement_status  = req_status,
            file                = uploaded_file,
            file_name           = uploaded_file.name if uploaded_file else "",
            file_url            = file_url,
            notes               = notes,
            uploaded_by         = request.user,
            verification_status = RequirementEvidence.VerificationStatus.PENDING,
            version_number      = next_version,
            is_latest           = True,
        )

        # Supersede previous latest
        if existing_latest:
            existing_latest.is_latest     = False
            existing_latest.superseded_by = evidence
            existing_latest.save(update_fields=["is_latest", "superseded_by", "updated_at"])

        # Update requirement status
        try:
            if req_status.status == ProjectRequirementStatus.Status.IN_PROGRESS:
                # Re-submission after rejection
                req_status.status     = ProjectRequirementStatus.Status.AWAITING_VERIFICATION
                req_status.updated_by = request.user
                req_status.save(update_fields=["status", "updated_by", "updated_at"])
                RequirementAudit.log(
                    requirement_status=req_status,
                    action=RequirementAudit.Action.EVIDENCE_UPLOADED,
                    changed_by=request.user,
                    notes=f"Bukti v{next_version} diunggah ulang setelah penolakan",
                )
            elif req_status.status not in (
                ProjectRequirementStatus.Status.COMPLETED,
                ProjectRequirementStatus.Status.AWAITING_VERIFICATION,
            ):
                req_status.mark_awaiting_verification(user=request.user)
        except ValueError as e:
            evidence.delete()
            return Response({"success": False, "message": str(e), "error_type": "dependency_blocked"}, status=status.HTTP_400_BAD_REQUEST)

        version_msg = f" (v{next_version})" if next_version > 1 else ""
        return Response({
            "success":         True,
            "message":         f"Bukti untuk '{req_status.requirement.name}' berhasil diunggah{version_msg}",
            "evidence":        RequirementEvidenceSerializer(evidence, context={"request": request}).data,
            "intelligence":    project.get_intelligence_summary(),
            "version_number":  next_version,
            "is_resubmission": next_version > 1,
        }, status=status.HTTP_201_CREATED)


# =============================================================================
# Sprint 8: Evidence verify — with self-verify guard
# =============================================================================

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

        # ── Sprint 8: self-verify guard ───────────────────────
        can_verify, reason = evidence.can_verify(request.user)
        if not can_verify:
            return Response({"success": False, "message": reason, "error_type": "cannot_verify"}, status=status.HTTP_400_BAD_REQUEST)

        project.snapshot_readiness()

        try:
            if action == "approve":
                evidence.approve(verifier_user=request.user, notes=notes)
                message = f"Bukti v{evidence.version_number} disetujui — requirement '{req_status.requirement.name}' selesai"
            else:
                evidence.reject(verifier_user=request.user, notes=notes)
                message = f"Bukti v{evidence.version_number} ditolak — developer perlu mengunggah ulang"
        except ValueError as e:
            return Response({"success": False, "message": str(e), "error_type": "dependency_blocked"}, status=status.HTTP_400_BAD_REQUEST)

        project.snapshot_risk()
        return Response({
            "success":      True,
            "message":      message,
            "evidence":     RequirementEvidenceSerializer(evidence, context={"request": request}).data,
            "intelligence": project.get_intelligence_summary(),
        })


# =============================================================================
# Sprint 8: NEW — Eligible verifiers for evidence
# =============================================================================

class EvidenceEligibleVerifiersView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk, req_status_id, ev_id):
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)
        try:
            evidence = RequirementEvidence.objects.get(id=ev_id, requirement_status=req_status)
        except RequirementEvidence.DoesNotExist:
            return Response({"success": False, "message": "Bukti tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        eligible           = evidence.get_eligible_verifiers()
        can_verify, reason = evidence.can_verify(request.user)

        return Response({
            "success":                    True,
            "evidence_id":                str(evidence.id),
            "version_number":             evidence.version_number,
            "eligible_verifiers":         [{"id": str(m.id), "full_name": m.full_name, "email": m.email} for m in eligible],
            "eligible_count":             eligible.count(),
            "can_verify_as_current_user": can_verify,
            "reason":                     reason,
        })


# ==================================================
# Sprint 3: Activity + Financial (unchanged)
# ==================================================

class ProjectActivityView(TenantScopedAPIView):
    """
    Sprint 3: Activity timeline for a project.
    Sprint 12: adds ?type= filter for Evidence / Kesiapan / Penugasan / Komentar.

    GET /api/projects/<id>/activity/?limit=20&type=all

    Query params:
      limit (int, 1-100, default 20)
      type  (str, default "all"):
        "all"         — no filter, all action types
        "evidence"    — evidence_uploaded, evidence_approved, evidence_rejected
        "readiness"   — completed, stage_advanced, updated
        "assignments" — assigned, due_date_set
        "comments"    — comment_added

    Response:
      {
        "success":      true,
        "project_id":   "uuid",
        "project_name": "Perumahan Asri Cluster A",
        "count":        12,
        "filter_type":  "evidence",
        "results":      [...]
      }
    """
    model = Project

    # Map frontend filter key → RequirementAudit.Action values
    ACTION_FILTER_MAP = {
        "evidence":    ["evidence_uploaded", "evidence_approved", "evidence_rejected"],
        "readiness":   ["completed", "stage_advanced", "updated"],
        "assignments": ["assigned", "due_date_set"],
        "comments":    ["comment_added"],
    }

    def get(self, request, pk):
        project     = self.get_object(pk)
        limit       = min(int(request.query_params.get("limit", 20)), 100)
        filter_type = request.query_params.get("type", "all")
        # None = no filter (all types) — model handles this correctly
        action_filter = self.ACTION_FILTER_MAP.get(filter_type)
        activities  = project.activity_timeline(limit=limit, action_filter=action_filter)
        return Response({
            "success":      True,
            "project_id":   str(project.id),
            "project_name": project.name,
            "count":        len(activities),
            "filter_type":  filter_type,
            "results":      activities,
        })

class ProjectFinancialView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        snapshot = project.financial_snapshot()
        return Response({"success": True, "project_id": str(project.id), "project_name": project.name, "financial": snapshot})
    
class ProjectDependencyGraphView(TenantScopedAPIView):
    """
    Sprint 11: Visual dependency graph data for the current stage.
    Transforms get_intelligence_summary() requirements into nodes + edges.

    GET /api/projects/<id>/dependency-graph/

    Response:
      {
        "success":      true,
        "project_id":   "uuid",
        "project_name": "Perumahan Asri Cluster A",
        "stage":        "konstruksi",
        "nodes": [
          {
            "id":                    "uuid",
            "name":                  "Kontraktor",
            "status":                "in_progress",
            "status_display":        "Sedang Diproses",
            "is_mandatory":          true,
            "is_blocking":           true,
            "is_dependency_blocked": false,
            "weight_pct":            60,
            "prerequisites":         [],
            "unmet_prerequisites":   []
          }
        ],
        "edges": [
          { "from": "uuid-a", "to": "uuid-b" }
        ]
      }

    Design decisions:
    - Reuses get_intelligence_summary() as single source of truth.
      All blocking/dependency state is already computed there.
    - edges derived from prerequisites[] — the Sprint 4 M2M field.
    - No new migration. No new model. Pure computation.
    - Tenant isolation guaranteed by TenantScopedAPIView.get_object(pk).
    """
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        intel   = project.get_intelligence_summary()
        requirements = intel["requirements"]

        # Build name→id map for edge resolution
        name_to_id = {req["name"]: req["id"] for req in requirements}

        # Build nodes — derive is_blocking from existing intelligence fields
        nodes = []
        for req in requirements:
            is_blocking = (
                req["is_mandatory"]
                and req["status"] not in ("completed", "menunggu_verifikasi")
                and not req["is_dependency_blocked"]
            )
            nodes.append({
                "id":                    req["id"],
                "name":                  req["name"],
                "status":                req["status"],
                "status_display":        req["status_display"],
                "is_mandatory":          req["is_mandatory"],
                "is_blocking":           is_blocking,
                "is_dependency_blocked": req["is_dependency_blocked"],
                "weight_pct":            req["weight_pct"],
                "prerequisites":         req["prerequisites"],
                "unmet_prerequisites":   req["unmet_prerequisites"],
            })

        # Build edges from prerequisite relationships
        edges = []
        for req in requirements:
            for prereq_name in req["prerequisites"]:
                from_id = name_to_id.get(prereq_name)
                if from_id:
                    edges.append({
                        "from": from_id,
                        "to":   req["id"],
                    })

        return Response({
            "success":      True,
            "project_id":   str(project.id),
            "project_name": project.name,
            "stage":        project.stage,
            "stage_display": project.stage_display,
            "nodes":        nodes,
            "edges":        edges,
        })

class ProjectReadinessHistoryView(TenantScopedAPIView):
    """
    Sprint 10: 30-day (default) readiness score history for the trend chart.
    Reads from ReadinessSnapshot — populated daily by snapshot_readiness().

    GET /api/projects/<id>/readiness-history/?days=30

    Query params:
      days (int, 1-90, default 30) — how far back to look

    Response:
      {
        "success":       true,
        "project_id":    "uuid",
        "project_name":  "Perumahan Asri Cluster A",
        "current_score": 65,
        "days":          30,
        "results": [
          {"date": "2026-06-01", "score": 40},
          {"date": "2026-06-15", "score": 52},
          ...
        ]
      }

    Notes:
    - If no snapshots exist yet (first run), returns empty results list.
      The frontend handles this gracefully — shows "not enough data yet".
    - Tenant isolation is guaranteed by TenantScopedAPIView.get_object(pk).
    """
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)

        # Cap days to 90 to keep response lean — 90 data points max
        try:
            days = max(1, min(int(request.query_params.get("days", 30)), 90))
        except (ValueError, TypeError):
            days = 30

        from datetime import timedelta
        cutoff    = date.today() - timedelta(days=days)
        snapshots = (
            project.readiness_snapshots
            .filter(snapped_at__gte=cutoff)
            .order_by("snapped_at")
            .values("snapped_at", "score")
        )

        return Response({
            "success":       True,
            "project_id":    str(project.id),
            "project_name":  project.name,
            "current_score": project.readiness_score,
            "days":          days,
            "results": [
                {"date": s["snapped_at"].isoformat(), "score": s["score"]}
                for s in snapshots
            ],
        })