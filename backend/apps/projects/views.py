# =============================================================================
# === backend/apps/projects/views.py ===
# Sprint 7: adds AssignRequirementView + RequirementCommentView
# All Sprint 1-6 views preserved — additive only.
# =============================================================================
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


# =============================================================================
# Sprint 7: NEW — Assign requirement + set due_date
# =============================================================================

class AssignRequirementView(TenantScopedAPIView):
    """
    Sprint 7: Assign a requirement to an org member and/or set due_date.

    PUT /api/projects/<id>/requirements/<req_status_id>/assign/
    Body: {
      "assigned_to": "<user_uuid>" | null,
      "due_date":    "YYYY-MM-DD"  | null
    }

    Rules:
    - Only org members (developer role) can be assigned
    - assigned_to must belong to same organization as project
    - due_date can be set independently of assigned_to
    - Both can be null (clears assignment / deadline)
    - Logs ASSIGNED and/or DUE_DATE_SET to RequirementAudit
    """
    model = Project

    def put(self, request, pk, req_status_id):
        if request.user.role not in ("developer", "super_admin"):
            return Response({"success": False, "message": "Tidak memiliki izin"}, status=status.HTTP_403_FORBIDDEN)

        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        assigned_to_id = request.data.get("assigned_to")   # UUID string or null
        due_date_str   = request.data.get("due_date")       # "YYYY-MM-DD" or null

        update_fields  = ["updated_at"]
        changed        = False

        # ── Validate + set assigned_to ────────────────────────
        if "assigned_to" in request.data:
            if assigned_to_id is None:
                # Clear assignment
                old_name = req_status.assigned_to.full_name if req_status.assigned_to else None
                req_status.assigned_to = None
                update_fields.append("assigned_to")
                if old_name:
                    RequirementAudit.log(
                        requirement_status=req_status,
                        action=RequirementAudit.Action.ASSIGNED,
                        changed_by=request.user,
                        old_value=old_name,
                        new_value="",
                        notes="Penugasan dibatalkan",
                    )
                changed = True
            else:
                # Validate: user must be org member
                org_members = project.get_org_members()
                try:
                    assignee = org_members.get(id=assigned_to_id)
                except Exception:
                    return Response({
                        "success": False,
                        "message": "Pengguna tidak ditemukan atau bukan anggota organisasi ini",
                    }, status=status.HTTP_400_BAD_REQUEST)

                old_name = req_status.assigned_to.full_name if req_status.assigned_to else None
                req_status.assigned_to = assignee
                update_fields.append("assigned_to")
                RequirementAudit.log(
                    requirement_status=req_status,
                    action=RequirementAudit.Action.ASSIGNED,
                    changed_by=request.user,
                    old_value=old_name or "",
                    new_value=assignee.full_name,
                    notes=f"Ditugaskan ke {assignee.full_name}",
                )
                changed = True

        # ── Validate + set due_date ───────────────────────────
        if "due_date" in request.data:
            if due_date_str is None:
                old_due = req_status.due_date.isoformat() if req_status.due_date else None
                req_status.due_date = None
                update_fields.append("due_date")
                if old_due:
                    RequirementAudit.log(
                        requirement_status=req_status,
                        action=RequirementAudit.Action.DUE_DATE_SET,
                        changed_by=request.user,
                        old_value=old_due,
                        new_value="",
                        notes="Tenggat waktu dihapus",
                    )
                changed = True
            else:
                from datetime import date as date_type
                try:
                    from datetime import datetime
                    new_due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except ValueError:
                    return Response({
                        "success": False,
                        "message": "Format tanggal tidak valid. Gunakan YYYY-MM-DD",
                    }, status=status.HTTP_400_BAD_REQUEST)

                old_due = req_status.due_date.isoformat() if req_status.due_date else None
                req_status.due_date = new_due
                update_fields.append("due_date")
                RequirementAudit.log(
                    requirement_status=req_status,
                    action=RequirementAudit.Action.DUE_DATE_SET,
                    changed_by=request.user,
                    old_value=old_due or "",
                    new_value=due_date_str,
                    notes=f"Tenggat waktu ditetapkan: {due_date_str}",
                )
                changed = True

        if not changed:
            return Response({"success": False, "message": "Tidak ada perubahan yang dikirim"}, status=status.HTTP_400_BAD_REQUEST)

        req_status.save(update_fields=list(set(update_fields)))

        return Response({
            "success":      True,
            "message":      f"Requirement '{req_status.requirement.name}' diperbarui",
            "intelligence": project.get_intelligence_summary(),
        })


# =============================================================================
# Sprint 7: NEW — Requirement comments
# =============================================================================

class RequirementCommentView(TenantScopedAPIView):
    """
    Sprint 7: Team discussion thread per requirement.

    GET  /api/projects/<id>/requirements/<req_status_id>/comments/
      Returns all comments for a requirement, oldest first.

    POST /api/projects/<id>/requirements/<req_status_id>/comments/
      Body: { "body": "..." }
      Creates a new comment. Author = request.user.
      Only org members can comment.
    """
    model = Project

    def get(self, request, pk, req_status_id):
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(id=req_status_id, project=project)
        except ProjectRequirementStatus.DoesNotExist:
            return Response({"success": False, "message": "Requirement tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        comments = req_status.comments.select_related("author").order_by("created_at")
        serializer = RequirementCommentSerializer(comments, many=True)
        return Response({
            "success":          True,
            "requirement_name": req_status.requirement.name,
            "count":            comments.count(),
            "results":          serializer.data,
        })

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

        comment = RequirementComment.objects.create(
            requirement_status=req_status,
            author=request.user,
            body=body,
        )

        RequirementAudit.log(
            requirement_status=req_status,
            action=RequirementAudit.Action.COMMENT_ADDED,
            changed_by=request.user,
            notes=body[:100] + ("..." if len(body) > 100 else ""),
        )

        serializer = RequirementCommentSerializer(comment)
        return Response({
            "success": True,
            "message": "Komentar berhasil ditambahkan",
            "comment": serializer.data,
        }, status=status.HTTP_201_CREATED)


# =============================================================================
# Sprint 7: NEW — Org members list (for assignee dropdown)
# =============================================================================

class ProjectOrgMembersView(TenantScopedAPIView):
    """
    Sprint 7: Returns list of org members who can be assigned to requirements.
    Used by the frontend assignee dropdown.

    GET /api/projects/<id>/members/
    Returns: [{ id, full_name, email, role }]
    """
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        members = project.get_org_members()
        results = [
            {
                "id":        str(m.id),
                "full_name": m.full_name,
                "email":     m.email,
                "role":      m.role,
            }
            for m in members
        ]
        return Response({
            "success": True,
            "count":   len(results),
            "results": results,
        })


# =============================================================================
# Sprint 2-3 evidence views — unchanged
# =============================================================================

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
            requirement_status=req_status, file=uploaded_file,
            file_name=uploaded_file.name if uploaded_file else "",
            file_url=file_url, notes=notes, uploaded_by=request.user,
            verification_status=RequirementEvidence.VerificationStatus.PENDING,
        )
        try:
            if req_status.status not in (ProjectRequirementStatus.Status.COMPLETED, ProjectRequirementStatus.Status.AWAITING_VERIFICATION):
                req_status.mark_awaiting_verification(user=request.user)
        except ValueError as e:
            evidence.delete()
            return Response({"success": False, "message": str(e), "error_type": "dependency_blocked"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "message": f"Bukti untuk '{req_status.requirement.name}' berhasil diunggah", "evidence": RequirementEvidenceSerializer(evidence).data, "intelligence": project.get_intelligence_summary()}, status=status.HTTP_201_CREATED)


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
        project.snapshot_risk()
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
