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
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        project = self.get_object(pk)
        try:
            req_status = ProjectRequirementStatus.objects.get(
                id=req_status_id, project=project
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
            return Response(
                {"success": False, "message": f"Status tidak valid. Pilihan: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = req_status.status

        # ── Sprint 16: capture BEFORE state ────────────────────────
        readiness_before = project.readiness_score
        risk_before      = project._get_risk_data()["score"]

        # ── Sprint 20: snapshot which requirements are dependency-
        # blocked BEFORE the change, so we can tell which ones just
        # got unlocked as a side effect of this specific action.
        requirements_before = {
            r["id"]: r["is_dependency_blocked"]
            for r in project.get_intelligence_summary()["requirements"]
        }

        project.snapshot_readiness()   # existing — unchanged

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
            return Response(
                {"success": False, "message": str(e), "error_type": "dependency_blocked"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project.snapshot_risk()   # existing — unchanged

        # ── Sprint 16: capture AFTER state + store impact ────────────
        readiness_after = project.readiness_score
        risk_after      = project._get_risk_data()["score"]

        # Update the most recently created audit log with impact data.
        # This works for both mark_completed() (which creates its own log)
        # and the manual RequirementAudit.log() call above.
        try:
            latest_log = req_status.audit_logs.first()   # ordered by -changed_at
            if latest_log and latest_log.readiness_before is None:
                latest_log.readiness_before = readiness_before
                latest_log.readiness_after  = readiness_after
                latest_log.risk_before      = risk_before
                latest_log.risk_after       = risk_after
                latest_log.save(update_fields=[
                    "readiness_before", "readiness_after",
                    "risk_before",      "risk_after",
                ])
        except Exception:
            pass

        # Build impact summary for the response
        readiness_delta = readiness_after - readiness_before
        risk_delta      = risk_after - risk_before

        intel = project.get_intelligence_summary()
        stage_can_advance = intel["blocking_count"] == 0

        # ── Sprint 20: newly_unlocked — requirements that were
        # dependency-blocked before this action and aren't anymore.
        # Only meaningful when completing something (other status
        # changes don't clear prerequisites for anything downstream).
        newly_unlocked = []
        if new_status == ProjectRequirementStatus.Status.COMPLETED:
            newly_unlocked = [
                r["name"] for r in intel["requirements"]
                if requirements_before.get(r["id"]) is True
                and not r["is_dependency_blocked"]
            ]

        # ── Sprint 20: dynamic, impact-aware message ("the dopamine
        # sprint" — the co-founders wanted the platform to feel alive
        # when an action changes reality, not just report a generic
        # 'updated' confirmation).
        if new_status == ProjectRequirementStatus.Status.COMPLETED:
            parts = [f"{req_status.requirement.name} selesai!"]
            if newly_unlocked:
                parts.append(f"{', '.join(newly_unlocked)} sekarang terbuka.")
            if stage_can_advance:
                parts.append("Tahap siap dilanjutkan. 🎉")
            impact_message = " ".join(parts)
        else:
            impact_message = f"Requirement '{req_status.requirement.name}' diperbarui"

        return Response({
            "success": True,
            "message": f"Requirement '{req_status.requirement.name}' diperbarui",
            # Sprint 16: impact data in response for frontend feedback loop
            # Sprint 20: + newly_unlocked, + impact-specific message
            "impact": {
                "readiness_before":  readiness_before,
                "readiness_after":   readiness_after,
                "readiness_delta":   readiness_delta,
                "risk_before":       risk_before,
                "risk_after":        risk_after,
                "risk_delta":        risk_delta,
                "stage_can_advance": stage_can_advance,
                "newly_unlocked":    newly_unlocked,
                "message":           impact_message,
            },
            "intelligence": intel,
        })


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

        # ── Sprint 16 fix: capture BEFORE state ─────────────────
        # (mirrors the working pattern already used in
        # ProjectRequirementUpdateView.put() — evidence upload was
        # the one status-changing path that never wired this in,
        # which is why Cause & Effect delta badges never rendered
        # for "mengunggah bukti" events on prod)
        readiness_before = project.readiness_score
        risk_before      = project._get_risk_data()["score"]

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

        # ── Sprint 16 fix: capture AFTER state + patch latest log ──
        readiness_after = project.readiness_score
        risk_after      = project._get_risk_data()["score"]
        try:
            latest_log = req_status.audit_logs.first()   # ordered by -changed_at
            if latest_log and latest_log.readiness_before is None:
                latest_log.readiness_before = readiness_before
                latest_log.readiness_after  = readiness_after
                latest_log.risk_before      = risk_before
                latest_log.risk_after       = risk_after
                latest_log.save(update_fields=[
                    "readiness_before", "readiness_after",
                    "risk_before",      "risk_after",
                ])
        except Exception:
            pass

        # ── Sprint 20: surface impact in the response too — this
        # data was already being captured (Sprint 16 fix), just never
        # returned. Without this, the frontend feedback loop would
        # only ever animate for the rarely-used direct status-update
        # endpoint and stay silent for the endpoint people actually
        # use every day (uploading evidence).
        # newly_unlocked is always empty here: uploading evidence
        # moves a requirement to AWAITING_VERIFICATION, never
        # COMPLETED, so nothing downstream can unlock from this
        # action specifically — that only happens on verify/approve.
        intel = project.get_intelligence_summary()
        version_msg = f" (v{next_version})" if next_version > 1 else ""
        return Response({
            "success":         True,
            "message":         f"Bukti untuk '{req_status.requirement.name}' berhasil diunggah{version_msg}",
            "evidence":        RequirementEvidenceSerializer(evidence, context={"request": request}).data,
            "intelligence":    intel,
            "version_number":  next_version,
            "is_resubmission": next_version > 1,
            "impact": {
                "readiness_before":  readiness_before,
                "readiness_after":   readiness_after,
                "readiness_delta":   readiness_after - readiness_before,
                "risk_before":       risk_before,
                "risk_after":        risk_after,
                "risk_delta":        risk_after - risk_before,
                "stage_can_advance": intel["blocking_count"] == 0,
                "newly_unlocked":    [],
                "message":           f"Bukti untuk '{req_status.requirement.name}' diunggah — menunggu verifikasi",
            },
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

        # ── Sprint 16 fix: capture BEFORE state ─────────────────
        # This is the moment that actually matters most for Cause &
        # Effect badges — approving evidence is what fires
        # mark_completed() and genuinely moves readiness/risk. It had
        # the exact same gap as the upload endpoint: never wired in.
        from django.utils import timezone
        readiness_before = project.readiness_score
        risk_before      = project._get_risk_data()["score"]
        snapshot_cutoff  = timezone.now()

        # ── Sprint 20: snapshot dependency-blocked state BEFORE the
        # action, same as ProjectRequirementUpdateView — only approve()
        # can complete a requirement and unlock anything downstream;
        # reject() never does.
        requirements_before = {
            r["id"]: r["is_dependency_blocked"]
            for r in project.get_intelligence_summary()["requirements"]
        }

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

        # ── Sprint 16 fix: capture AFTER state + patch every log this
        # action created. approve() creates TWO audit logs (COMPLETED,
        # then EVIDENCE_APPROVED) — patch both, not just the latest,
        # so the badge isn't lost depending on which line the frontend
        # happens to render.
        readiness_after = project.readiness_score
        risk_after      = project._get_risk_data()["score"]
        try:
            new_logs = list(req_status.audit_logs.filter(
                changed_at__gte=snapshot_cutoff,
                readiness_before__isnull=True,
            ))
            for log in new_logs:
                log.readiness_before = readiness_before
                log.readiness_after  = readiness_after
                log.risk_before      = risk_before
                log.risk_after       = risk_after
            if new_logs:
                RequirementAudit.objects.bulk_update(
                    new_logs,
                    ["readiness_before", "readiness_after", "risk_before", "risk_after"],
                )
        except Exception:
            pass

        intel = project.get_intelligence_summary()
        stage_can_advance = intel["blocking_count"] == 0

        # ── Sprint 20: newly_unlocked, only meaningful on approve
        # (reject never completes anything, so nothing can unlock)
        newly_unlocked = []
        if action == "approve":
            newly_unlocked = [
                r["name"] for r in intel["requirements"]
                if requirements_before.get(r["id"]) is True
                and not r["is_dependency_blocked"]
            ]

        if action == "approve":
            parts = [f"Bukti v{evidence.version_number} disetujui — {req_status.requirement.name} selesai!"]
            if newly_unlocked:
                parts.append(f"{', '.join(newly_unlocked)} sekarang terbuka.")
            if stage_can_advance:
                parts.append("Tahap siap dilanjutkan. 🎉")
            impact_message = " ".join(parts)
        else:
            impact_message = message   # reject: keep the existing plain message

        return Response({
            "success":      True,
            "message":      message,
            "evidence":     RequirementEvidenceSerializer(evidence, context={"request": request}).data,
            "intelligence": intel,
            "impact": {
                "readiness_before":  readiness_before,
                "readiness_after":   readiness_after,
                "readiness_delta":   readiness_after - readiness_before,
                "risk_before":       risk_before,
                "risk_after":        risk_after,
                "risk_delta":        risk_after - risk_before,
                "stage_can_advance": stage_can_advance,
                "newly_unlocked":    newly_unlocked,
                "message":           impact_message,
            },
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

            # Sprint 16: block reason from unmet prerequisites
            unmet = req.get("unmet_prerequisites", [])
            block_reason = (
                f"Selesaikan dulu: {', '.join(unmet)}"
                if unmet else None
            )

            # Sprint 16: estimated minutes from current state (same as Decision Engine)
            est = (
                (5 if not req.get("assigned_to_id") else 0) +
                (7 if req.get("evidence_count", 0) == 0 else 0) +
                (3 if req.get("evidence_count", 0) > 0 else 0) +
                2
            )

            nodes.append({
                # ── Sprint 1-11 fields (unchanged) ──
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
                # ── Sprint 16: interactive detail fields ──
                "block_reason":          block_reason,
                "assigned_to_name":      req.get("assigned_to_name"),
                "est_minutes":           est,
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
    
class ProjectDecisionEngineView(TenantScopedAPIView):
    """
    Sprint 13: Decision Engine — ranked recommendations with quantified impact.

    GET /api/projects/<id>/decision/

    Response (blocked project):
      {
        "success":            true,
        "project_id":         "uuid",
        "project_name":       "Perumahan Asri Cluster A",
        "has_recommendations": true,
        "all_clear":           false,
        "current_readiness":   40,
        "projected_readiness": 100,
        "primary": {
          "requirement_name":     "Kontraktor",
          "requirement_id":       "uuid",
          "status_id":            "uuid",
          "action":               "Selesaikan Kontraktor",
          "priority":             "high",
          "readiness_impact_pct": 60,
          "est_minutes":          17,
          "reasons": [
            "Menyelesaikan ini meningkatkan kesiapan sebesar 60%",
            "Memblokir 1 requirement lain: Jadwal proyek",
            "Belum ada anggota tim yang ditugaskan"
          ],
          "is_assigned":   false,
          "evidence_count": 1
        },
        "alternatives": [
          {
            "rank":                 2,
            "requirement_name":     "Rencana Kerja",
            "action":               "Selesaikan Rencana Kerja",
            "readiness_impact_pct": 40,
            "est_minutes":          12
          }
        ]
      }

    Response (all clear):
      {
        "success":            true,
        "has_recommendations": false,
        "all_clear":           true,
        "primary":             null,
        "alternatives":        [],
        "current_readiness":   100,
        "projected_readiness": 100,
        "message":             "Semua requirement wajib sudah selesai! 🎉"
      }

    Design:
    - Pure computation via Project.get_decision_engine()
    - Deterministic, auditable — every number is arithmetic on weight_pct
    - Tenant isolation via TenantScopedAPIView.get_object(pk)
    - No new migration, no new model
    """
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        engine  = project.get_decision_engine()
        return Response({
            "success":      True,
            "project_id":   str(project.id),
            "project_name": project.name,
            **engine,
        })

class ProjectRiskForecastView(TenantScopedAPIView):
    """
    Sprint 14: 14-day risk forecast — what happens to the risk score
    if nothing changes in the next N days.

    GET /api/projects/<id>/risk-forecast/?days=14

    Query params:
      days (int, 1-30, default 14) — how far ahead to project

    Response:
      {
        "success":       true,
        "project_id":    "uuid",
        "project_name":  "Perumahan Asri Cluster A",
        "days":          14,
        "current": {
          "score": 30,  "level": "medium",  "level_display": "Sedang"
        },
        "forecast": {
          "score": 34,  "level": "medium",  "level_display": "Sedang"
        },
        "delta":         4,
        "will_escalate": false,
        "top_drivers": [
          {
            "key":             "timeline_overrun",
            "name":            "Terlambat 210 hari",
            "description":     "Proyek melewati target selesai 210 hari...",
            "impact":          "Tinggi",
            "current_points":  20,
            "forecast_points": 20,
            "delta_points":    0,
            "is_new":          false
          }
        ]
      }

    Design:
    - Calls _get_risk_data() + _get_forecast_risk_data() — pure computation.
    - delta = forecast.score - current.score (always >= 0 for time-based growth)
    - will_escalate = level increases (low→medium or medium→high)
    - top_drivers = all factors present in forecast, sorted by forecast_points desc
    - is_new = factor wasn't present in current but appears in forecast
      (e.g. a project that isn't overdue today but WILL be in 14 days)
    - Tenant isolation via TenantScopedAPIView.get_object(pk)
    - Zero new migration. Zero new model.
    """
    model = Project

    LEVEL_DISPLAY = {"low": "Rendah", "medium": "Sedang", "high": "Tinggi"}
    LEVEL_ORDER   = {"low": 0, "medium": 1, "high": 2}

    def get(self, request, pk):
        project = self.get_object(pk)

        try:
            days = max(1, min(int(request.query_params.get("days", 14)), 30))
        except (ValueError, TypeError):
            days = 14

        current_data  = project._get_risk_data()
        forecast_data = project._get_forecast_risk_data(days=days)

        # ── Build top_drivers ────────────────────────────────────
        # Map factor key → points for quick lookup
        current_map  = {f["key"]: f for f in current_data["factors"]}
        forecast_map = {f["key"]: f for f in forecast_data["factors"]}

        # Include all factors that appear in the forecast
        top_drivers = []
        for key, fore in forecast_map.items():
            curr      = current_map.get(key)
            curr_pts  = curr["points"] if curr else 0
            fore_pts  = fore["points"]
            top_drivers.append({
                "key":             key,
                "name":            fore["name"],
                "description":     fore["description"],
                "impact":          fore["impact"],
                "current_points":  curr_pts,
                "forecast_points": fore_pts,
                "delta_points":    fore_pts - curr_pts,
                "is_new":          curr is None,
            })

        top_drivers.sort(key=lambda d: d["forecast_points"], reverse=True)

        # ── Escalation check ─────────────────────────────────────
        current_level  = current_data["level"]
        forecast_level = forecast_data["level"]
        will_escalate  = (
            self.LEVEL_ORDER.get(forecast_level, 0) >
            self.LEVEL_ORDER.get(current_level, 0)
        )

        return Response({
            "success":      True,
            "project_id":   str(project.id),
            "project_name": project.name,
            "days":         days,
            "current": {
                "score":         current_data["score"],
                "level":         current_level,
                "level_display": self.LEVEL_DISPLAY.get(current_level, current_level),
            },
            "forecast": {
                "score":         forecast_data["score"],
                "level":         forecast_level,
                "level_display": self.LEVEL_DISPLAY.get(forecast_level, forecast_level),
            },
            "delta":         forecast_data["score"] - current_data["score"],
            "will_escalate": will_escalate,
            "top_drivers":   top_drivers,
        })
    
class ProjectPulseView(TenantScopedAPIView):
    """
    Sprint 17: Lightweight polling endpoint for smart live updates.
    Called by frontend every 15 seconds. Returns ONLY events since `since`.

    GET /api/projects/<id>/pulse/?since=<iso_timestamp>

    Query params:
      since (ISO datetime, optional) — return only events after this time.
             If missing or invalid → returns last 5 events.

    Response:
      {
        "success":               true,
        "project_id":            "uuid",
        "has_updates":           true,
        "readiness_score":       65,
        "readiness_delta_today": 6,    (null if no yesterday snapshot)
        "risk_score":            30,
        "blocking_count":        1,
        "new_events": [
          {
            "id":              "uuid",
            "action":          "evidence_uploaded",
            "message":         "Budi mengunggah bukti untuk Kontraktor",
            "actor":           "Budi Developer",
            "subject":         "Kontraktor",
            "readiness_delta": 0,
            "risk_delta":      null,
            "timestamp":       "2026-07-03T09:18:00+00:00"
          }
        ],
        "checked_at": "2026-07-03T09:20:00+00:00"
      }

    Design:
    - Extremely lightweight — one filtered queryset + project properties.
    - has_updates=false means frontend skips re-rendering — no wasted cycles.
    - readiness_delta_today: compares current score vs yesterday's snapshot.
    - Tenant isolation via TenantScopedAPIView.get_object(pk).
    - Zero new migration.
    """
    model = Project

    ACTION_LABELS = {
        "created":           "membuat requirement",
        "updated":           "memperbarui",
        "evidence_uploaded": "mengunggah bukti untuk",
        "evidence_approved": "menyetujui bukti",
        "evidence_rejected":  "menolak bukti",
        "completed":         "menyelesaikan",
        "stage_advanced":    "melanjutkan tahap ke",
        "assigned":          "menugaskan",
        "due_date_set":      "menetapkan tenggat untuk",
        "comment_added":     "menambahkan komentar pada",
    }

    def get(self, request, pk):
        from datetime import date, timedelta
        from django.utils import timezone
        from django.utils.dateparse import parse_datetime

        project = self.get_object(pk)

        # ── Parse 'since' timestamp ────────────────────────────
        since = None
        since_param = request.query_params.get("since", "").strip()
        if since_param:
            try:
                since = parse_datetime(since_param.replace(" ", "+"))
            except (ValueError, TypeError):
                since = None

        # ── Fetch audit logs ───────────────────────────────────
        audit_qs = RequirementAudit.objects.filter(
            requirement_status__project=project
        ).select_related(
            "requirement_status__requirement", "changed_by"
        ).order_by("-changed_at")

        if since:
            audit_qs = audit_qs.filter(changed_at__gt=since)
            has_updates = audit_qs.exists()
        else:
            audit_qs = audit_qs[:5]
            has_updates = True

        # ── Build event list (max 10) ──────────────────────────
        events = []
        for log in audit_qs[:10]:
            req_name = log.requirement_status.requirement.name
            actor    = log.changed_by.full_name if log.changed_by else "Sistem"
            verb     = self.ACTION_LABELS.get(log.action, log.action)

            readiness_delta = (
                log.readiness_after - log.readiness_before
                if log.readiness_before is not None and log.readiness_after is not None
                else None
            )
            risk_delta = (
                log.risk_after - log.risk_before
                if log.risk_before is not None and log.risk_after is not None
                else None
            )

            events.append({
                "id":              str(log.id),
                "action":          log.action,
                "message":         f"{actor} {verb} {req_name}",
                "actor":           actor,
                "subject":         req_name,
                "readiness_delta": readiness_delta,
                "risk_delta":      risk_delta,
                "timestamp":       log.changed_at.isoformat(),
            })

        # ── Readiness delta today (vs yesterday's snapshot) ───
        yesterday = date.today() - timedelta(days=1)
        yesterday_snap = project.readiness_snapshots.filter(
            snapped_at=yesterday
        ).first()
        readiness_delta_today = (
            project.readiness_score - yesterday_snap.score
            if yesterday_snap else None
        )

        return Response({
            "success":               True,
            "project_id":            str(project.id),
            "has_updates":           has_updates,
            "readiness_score":       project.readiness_score,
            "readiness_delta_today": readiness_delta_today,
            "risk_score":            project._get_risk_data()["score"],
            "blocking_count":        project.blocking_count,
            "new_events":            events,
            "checked_at":            timezone.now().isoformat(),
        })


class ProjectRecentActivityView(TenantScopedAPIView):
    """
    Sprint 17: Cross-project recent activity feed for the main dashboard.
    Returns most recent events across ALL of the user's org projects.

    GET /api/projects/recent-activity/?limit=10

    Response:
      {
        "success": true,
        "count":   5,
        "results": [
          {
            "id":              "uuid",
            "action":          "completed",
            "message":         "Budi menyelesaikan Rencana kerja",
            "actor":           "Budi Developer",
            "subject":         "Rencana kerja",
            "project_id":      "uuid",
            "project_name":    "Perumahan Asri Cluster A",
            "readiness_delta": 40,
            "timestamp":       "2026-07-03T09:18:00+00:00"
          }
        ]
      }

    Design:
    - get_queryset() returns Project.objects.for_user(user) — tenant scoped.
    - Aggregates RequirementAudit across ALL org projects in one query.
    - Used for the cross-project event stream on the main dashboard page.
    - No new migration.
    """
    model = Project

    ACTION_LABELS = {
        "created":           "membuat requirement",
        "updated":           "memperbarui",
        "evidence_uploaded": "mengunggah bukti untuk",
        "evidence_approved": "menyetujui bukti",
        "evidence_rejected":  "menolak bukti",
        "completed":         "menyelesaikan",
        "stage_advanced":    "melanjutkan tahap ke",
        "assigned":          "menugaskan",
        "due_date_set":      "menetapkan tenggat untuk",
        "comment_added":     "menambahkan komentar pada",
    }

    def get(self, request):
        try:
            limit = max(1, min(int(request.query_params.get("limit", 10)), 50))
        except (ValueError, TypeError):
            limit = 10

        # Tenant-scoped: only projects belonging to user's org
        org_projects = self.get_queryset()

        audit_logs = RequirementAudit.objects.filter(
            requirement_status__project__in=org_projects
        ).select_related(
            "requirement_status__requirement",
            "requirement_status__project",
            "changed_by",
        ).order_by("-changed_at")[:limit]

        events = []
        for log in audit_logs:
            req_name     = log.requirement_status.requirement.name
            project_name = log.requirement_status.project.name
            project_id   = str(log.requirement_status.project.id)
            actor        = log.changed_by.full_name if log.changed_by else "Sistem"
            verb         = self.ACTION_LABELS.get(log.action, log.action)

            readiness_delta = (
                log.readiness_after - log.readiness_before
                if log.readiness_before is not None and log.readiness_after is not None
                else None
            )

            events.append({
                "id":              str(log.id),
                "action":          log.action,
                "message":         f"{actor} {verb} {req_name}",
                "actor":           actor,
                "subject":         req_name,
                "project_id":      project_id,
                "project_name":    project_name,
                "readiness_delta": readiness_delta,
                "timestamp":       log.changed_at.isoformat(),
            })

        return Response({
            "success": True,
            "count":   len(events),
            "results": events,
        })


class ProjectCalendarView(TenantScopedAPIView):
    """
    Sprint 19: Cross-project calendar — every requirement with a
    due_date set, across ALL of the user's org projects. Powers the
    standalone Calendar page in the new sidebar.

    GET /api/projects/calendar/

    Response:
      {
        "success": true,
        "count":   2,
        "results": [
          {
            "id":               "uuid",   (ProjectRequirementStatus id)
            "requirement_name": "Kontraktor",
            "project_id":       "uuid",
            "project_name":     "Perumahan Asri Cluster A",
            "due_date":         "2026-07-10",
            "status":           "in_progress",
            "is_overdue":       false,
            "days_until_due":   5,
            "assigned_to_name": "Budi Developer" | null
          }
        ]
      }

    Design:
    - Reuses the exact tenant-scoping pattern already proven in
      ProjectRecentActivityView above (self.get_queryset() →
      Project.objects.for_user(user)).
    - Shows ALL requirements with a due_date regardless of status —
      including COMPLETED — so the frontend can style them (e.g.
      greyed out) rather than the backend silently hiding history.
    - is_overdue / days_until_due reuse the exact computed properties
      that have existed on ProjectRequirementStatus since Sprint 7 —
      no new logic, no new migration.
    """
    model = Project

    def get(self, request):
        org_projects = self.get_queryset()

        statuses = ProjectRequirementStatus.objects.filter(
            project__in=org_projects,
            due_date__isnull=False,
        ).select_related(
            "requirement", "project", "assigned_to",
        ).order_by("due_date")

        events = []
        for s in statuses:
            events.append({
                "id":               str(s.id),
                "requirement_name": s.requirement.name,
                "project_id":       str(s.project.id),
                "project_name":     s.project.name,
                "due_date":         s.due_date.isoformat(),
                "status":           s.status,
                "is_overdue":       s.is_overdue,
                "days_until_due":   s.days_until_due,
                "assigned_to_name": s.assigned_to.full_name if s.assigned_to else None,
            })

        return Response({
            "success": True,
            "count":   len(events),
            "results": events,
        })


# SPRINT 18 - Portfolio Intelligence Hub (CEO Bloomberg View)
class PortfolioIntelligenceView(TenantScopedAPIView):
    """
    Sprint 18: Bloomberg-style portfolio intelligence for the CEO executive view.

    GET /api/projects/portfolio-intelligence/

    Response:
      {
        "success":     true,
        "current": {
          "total_projects":    3,
          "avg_readiness":     60.0,
          "critical_count":    1,
          "high_risk_count":   0,
          "delayed_count":     2,
          "revenue_protected": 46000000000,
          "revenue_this_month": 7200000,
          "ar_outstanding":    2000000
        },
        "week_delta": {
          "avg_readiness":   4.0,   (positive = improved)
          "critical_count": -1,     (negative = improved)
          "high_risk_count": 0,
          "delayed_count":   0
        },                          (null if no PortfolioSnapshot history yet)
        "top_at_risk": [
          {
            "id":           "uuid",
            "name":         "Perumahan Asri Cluster A",
            "readiness":    40,
            "risk_level":   "medium",
            "risk_display": "Sedang",
            "blocking":     1,
            "next_action":  "Kontraktor"
          }
        ],
        "has_history": false   (true after snapshot_portfolio_daily runs)
      }

    Design:
    - Current metrics computed LIVE from Project properties — always accurate.
    - week_delta from PortfolioSnapshot (7 days ago) — null on first run.
      Honest, never hallucinated. Run `snapshot_portfolio_daily` to populate.
    - top_at_risk: worst 3 projects by readiness with blockers/risk.
    - Tenant isolation via get_queryset() (Project.objects.for_user).
    - Sprint 26: revenue_protected = sum(Payment.amount) where
      status="lunas", portfolio-wide, all-time — real collected money,
      not planned budget (that was the old, misleading definition).
      revenue_this_month = same, filtered to paid_at in the current
      calendar month (via timezone.localtime(), not a naive UTC
      comparison — same bug class hardened in Sprint 25).
      ar_outstanding = sum(Payment.amount) where Payment.is_overdue,
      portfolio-wide — reuses the exact same property that already
      drives the per-project collection_efficiency figure, so the two
      numbers can never quietly disagree.
    """
    model = Project

    ACTIVE_STAGES = ("selesai", "serah_terima")  # exclude from revenue/delay count

    def get(self, request):
        from datetime import date, timedelta
        from apps.projects.models import PortfolioSnapshot

        projects = list(self.get_queryset())
        today    = date.today()

        # ── Empty org — return zeros ──────────────────────────────
        if not projects:
            return Response({
                "success":     True,
                "current":     {
                    "total_projects": 0, "avg_readiness": 0,
                    "critical_count": 0, "high_risk_count": 0,
                    "delayed_count": 0, "revenue_protected": 0,
                    "revenue_this_month": 0, "ar_outstanding": 0,
                },
                "week_delta":  None,
                "top_at_risk": [],
                "has_history": False,
            })

        # ── Current state (always live) ───────────────────────────
        total           = len(projects)
        readiness_sum   = sum(p.readiness_score for p in projects)
        avg_readiness   = round(readiness_sum / total, 1) if total else 0.0
        critical_count  = sum(1 for p in projects if p.blocking_count > 0)
        high_risk_count = sum(1 for p in projects if p.risk_level == "high")
        delayed_count   = sum(
            1 for p in projects
            if p.end_date
            and p.end_date < today
            and p.stage not in self.ACTIVE_STAGES
        )
        # Sprint 26: revenue_protected now means what it says — real
        # money actually collected (status="lunas"), portfolio-wide,
        # all-time. Previously this summed target_budget (planned
        # construction budget), which had zero connection to whether
        # a single Rupiah had ever been collected — same class of
        # honesty problem as the old collection_efficiency bug, just
        # under a more convincing label. revenue_this_month and
        # ar_outstanding are genuinely new; ar_outstanding reuses
        # Payment.is_overdue (hardened Sprint 25) so this portfolio
        # figure can never quietly disagree with the per-project
        # collection_efficiency number the same way total_arrears
        # used to before that fix.
        from apps.payments.models import Payment
        from django.utils import timezone

        portfolio_payments = list(
            Payment.objects.filter(unit__project__in=projects).select_related("unit")
        )
        revenue_protected = int(sum(
            p.amount for p in portfolio_payments if p.status == "lunas"
        ))
        revenue_this_month = int(sum(
            p.amount for p in portfolio_payments
            if p.status == "lunas" and p.paid_at
            and timezone.localtime(p.paid_at).year == today.year
            and timezone.localtime(p.paid_at).month == today.month
        ))
        ar_outstanding = int(sum(
            p.amount for p in portfolio_payments if p.is_overdue
        ))

        current = {
            "total_projects":     total,
            "avg_readiness":      avg_readiness,
            "critical_count":     critical_count,
            "high_risk_count":    high_risk_count,
            "delayed_count":      delayed_count,
            "revenue_protected":  revenue_protected,
            "revenue_this_month": revenue_this_month,
            "ar_outstanding":     ar_outstanding,
        }

        # ── Week delta from PortfolioSnapshot ─────────────────────
        week_delta  = None
        has_history = False

        org_id = projects[0].organization_id if projects else None
        if org_id:
            last_week  = today - timedelta(days=7)
            week_snap  = PortfolioSnapshot.objects.filter(
                organization_id=org_id,
                snapped_at__lte=last_week,
            ).order_by("-snapped_at").first()

            if week_snap:
                has_history = True
                week_delta  = {
                    "avg_readiness":   round(avg_readiness - week_snap.avg_readiness, 1),
                    "critical_count":  critical_count  - week_snap.critical_count,
                    "high_risk_count": high_risk_count - week_snap.high_risk_count,
                    "delayed_count":   delayed_count   - week_snap.delayed_count,
                }

        # ── Top at-risk projects (worst 3 by readiness + blockers) ──
        at_risk = sorted(
            [p for p in projects if p.blocking_count > 0 or p.risk_level in ("high", "medium")],
            key=lambda p: p.readiness_score,
        )[:3]

        top_at_risk = [
            {
                "id":           str(p.id),
                "name":         p.name,
                "readiness":    p.readiness_score,
                "risk_level":   p.risk_level,
                "risk_display": p.risk_level_display,
                "blocking":     p.blocking_count,
                "next_action":  p.next_action,
            }
            for p in at_risk
        ]

        return Response({
            "success":     True,
            "current":     current,
            "week_delta":  week_delta,
            "top_at_risk": top_at_risk,
            "has_history": has_history,
        })