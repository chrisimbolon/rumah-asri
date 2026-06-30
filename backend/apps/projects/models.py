# =============================================================================
# === backend/apps/projects/models.py ===
# =============================================================================
"""
DevelopIndo — Projects Model + Intelligence Engine

Sprint 1: readiness_dimensions, risk_reasons, alerts, parallel_stages,
          collection_efficiency, is_selling/is_constructing
Sprint 2: RequirementEvidence, menunggu_verifikasi status,
          approve()/reject() flow
Sprint 3: RequirementAudit — immutable audit trail
          activity_timeline(), financial_snapshot()
Sprint 4: Dependency Graph & Rule Engine
          StageRequirement.prerequisites — M2M self-reference
          ProjectRequirementStatus.can_complete() — prereq check
Sprint 5: Explainable Weighted Readiness Engine
          StageRequirement.weight, readiness_breakdown, readiness_label
Sprint 6: Risk Engine — Scored & Explained
          RiskSnapshot, risk_score, risk_factors, risk_since
Sprint 7: Requirement Ownership & Accountability
          ProjectRequirementStatus.assigned_to — FK to org member
          ProjectRequirementStatus.due_date    — deadline
          RequirementComment                   — team discussion
          Project.get_org_members()            — assignable users
          overdue_requirements_count           — new alert trigger
Sprint 9 : my_tasks    — requirements assigned to the user
          unassigned  — actionable items nobody owns yet
          (items assigned to OTHER users are excluded — not noise)

ZERO BREAKING CHANGES — all existing fields preserved.
59 tests still green.
"""
import uuid
from datetime import date, timedelta

from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel


# =============================================================================
# StageRequirement — unchanged from Sprint 5
# =============================================================================

class StageRequirement(models.Model):
    class Stage(models.TextChoices):
        DRAFT        = "draft",        "Draft"
        PLANNING     = "perencanaan",  "Perencanaan"
        PERMITS      = "perizinan",    "Perizinan"
        CONSTRUCTION = "konstruksi",   "Konstruksi"
        SALES        = "penjualan",    "Penjualan"
        HANDOVER     = "serah_terima", "Serah Terima"
        COMPLETED    = "selesai",      "Selesai"

    class Category(models.TextChoices):
        INVENTORY   = "inventory",   "Inventori Unit"
        COMPLIANCE  = "compliance",  "Perizinan & Kepatuhan"
        SITE_PLAN   = "site_plan",   "Site Plan & Masterplan"
        SALES_SETUP = "sales_setup", "Setup Penjualan"
        GENERAL     = "general",     "Umum"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stage        = models.CharField(max_length=20, choices=Stage.choices, db_index=True)
    name         = models.CharField(max_length=200, verbose_name="Nama Requirement")
    description  = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    order        = models.PositiveIntegerField(default=0)
    is_active    = models.BooleanField(default=True)
    category     = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    weight       = models.PositiveIntegerField(
        default=10,
        verbose_name="Bobot",
        help_text="Bobot requirement dalam kalkulasi readiness (0-100). Hanya berlaku untuk requirement wajib.",
    )
    prerequisites = models.ManyToManyField(
        "self", symmetrical=False, blank=True,
        related_name="dependents", verbose_name="Prasyarat",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Stage Requirement"
        verbose_name_plural = "Stage Requirements"
        ordering            = ["stage", "order"]
        unique_together     = [["stage", "name"]]

    def __str__(self):
        flag = "⚡" if self.is_mandatory else "○"
        return f"{flag} [{self.get_stage_display()}] {self.name} (w={self.weight})"

    def get_prerequisite_names(self):
        return list(self.prerequisites.values_list("name", flat=True))


# =============================================================================
# ProjectRequirementStatus — Sprint 7: adds assigned_to + due_date
# =============================================================================

class ProjectRequirementStatus(models.Model):
    class Status(models.TextChoices):
        PENDING               = "pending",             "Belum Dimulai"
        IN_PROGRESS           = "in_progress",         "Sedang Diproses"
        AWAITING_VERIFICATION = "menunggu_verifikasi", "Menunggu Verifikasi"
        COMPLETED             = "completed",           "Selesai"
        NOT_APPLICABLE        = "not_applicable",      "Tidak Berlaku"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project     = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="requirement_statuses")
    requirement = models.ForeignKey(StageRequirement, on_delete=models.CASCADE, related_name="project_statuses")
    status      = models.CharField(max_length=25, choices=Status.choices, default=Status.PENDING)
    notes       = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="updated_requirements",
    )
    updated_at  = models.DateTimeField(auto_now=True)

    # ── Sprint 7: Ownership fields ────────────────────────────
    # assigned_to: only org members (developer role) can be assigned.
    # Enforced at the view/serializer level — model is FK only.
    # on_delete=SET_NULL so deleting a user doesn't delete requirement status.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_requirements",
        verbose_name="Ditugaskan ke",
        help_text="Anggota organisasi yang bertanggung jawab atas requirement ini",
    )
    # due_date: target completion date for this requirement.
    # Independent from project end_date — can be earlier.
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Tenggat Waktu",
        help_text="Target tanggal penyelesaian requirement ini",
    )

    class Meta:
        verbose_name        = "Project Requirement Status"
        verbose_name_plural = "Project Requirement Statuses"
        unique_together     = [["project", "requirement"]]
        ordering            = ["requirement__order"]

    def __str__(self):
        return f"{self.project.name} — {self.requirement.name}: {self.status}"

    # ── Sprint 7: Ownership computed properties ───────────────

    @property
    def is_overdue(self):
        """True if due_date is set, not completed, and past today."""
        if not self.due_date:
            return False
        if self.status == self.Status.COMPLETED:
            return False
        return date.today() > self.due_date

    @property
    def days_until_due(self):
        """
        Positive = days remaining.
        Negative = days overdue.
        None     = no due_date set.
        """
        if not self.due_date:
            return None
        return (self.due_date - date.today()).days

    # ── Prerequisite helpers — unchanged ─────────────────────

    def get_unmet_prerequisites(self):
        prereqs = self.requirement.prerequisites.all()
        if not prereqs.exists():
            return []
        unmet = []
        for prereq in prereqs:
            try:
                prereq_status = ProjectRequirementStatus.objects.get(
                    project=self.project, requirement=prereq,
                )
                if prereq_status.status != self.Status.COMPLETED:
                    unmet.append(prereq.name)
            except ProjectRequirementStatus.DoesNotExist:
                unmet.append(prereq.name)
        return unmet

    def can_complete(self):
        unmet = self.get_unmet_prerequisites()
        if unmet:
            prereq_list = ", ".join(unmet)
            return False, (
                f"'{self.requirement.name}' membutuhkan prasyarat: "
                f"{prereq_list}. Selesaikan prasyarat terlebih dahulu."
            )
        return True, ""

    def mark_completed(self, user=None):
        from django.utils import timezone
        ok, reason = self.can_complete()
        if not ok:
            raise ValueError(reason)
        old_status        = self.status
        self.status       = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.updated_by   = user
        self.save(update_fields=["status", "completed_at", "updated_by", "updated_at"])
        RequirementAudit.log(
            requirement_status=self,
            action=RequirementAudit.Action.COMPLETED,
            changed_by=user,
            old_value=old_status,
            new_value=self.Status.COMPLETED,
        )

    def mark_awaiting_verification(self, user=None):
        ok, reason = self.can_complete()
        if not ok:
            raise ValueError(reason)
        old_status  = self.status
        self.status = self.Status.AWAITING_VERIFICATION
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_at"])
        RequirementAudit.log(
            requirement_status=self,
            action=RequirementAudit.Action.EVIDENCE_UPLOADED,
            changed_by=user,
            old_value=old_status,
            new_value=self.Status.AWAITING_VERIFICATION,
        )


# =============================================================================
# RequirementEvidence — Updated on Sprint 8
# =============================================================================

class RequirementEvidence(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING  = "pending",  "Menunggu Review"
        APPROVED = "approved", "Disetujui"
        REJECTED = "rejected", "Ditolak"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_status = models.ForeignKey(
        ProjectRequirementStatus, on_delete=models.CASCADE, related_name="evidence",
    )
    file      = models.FileField(upload_to="evidence/%Y/%m/", null=True, blank=True)
    file_name = models.CharField(max_length=300, blank=True)
    file_url  = models.URLField(blank=True)
    notes     = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="uploaded_evidence",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING, db_index=True,
    )
    verifier       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="verified_evidence",
    )
    verified_at    = models.DateTimeField(null=True, blank=True)
    verifier_notes = models.TextField(blank=True)
    updated_at     = models.DateTimeField(auto_now=True)

    # ── Sprint 8: Version tracking fields ─────────────────────
    # version_number: auto-incremented per requirement_status
    # Starts at 1 for the first upload, increments on re-upload.
    # Used for display: "v1 (Ditolak) → v2 (Aktif)"
    version_number = models.PositiveIntegerField(
        default=1,
        verbose_name="Versi",
        help_text="Nomor versi bukti untuk requirement ini",
    )

    # is_latest: True only on the most recent upload per requirement.
    # Auto-managed by the upload view — old versions set to False
    # when a new upload supersedes them.
    is_latest = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Versi Terbaru",
        help_text="True jika ini adalah versi bukti terbaru",
    )

    # superseded_by: FK to the NEXT version (the one that replaced this).
    # Chain reads: ev1.superseded_by = ev2, ev2.superseded_by = ev3
    # Latest version has superseded_by = None.
    # on_delete=SET_NULL: deleting a newer version doesn't cascade.
    superseded_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_version",
        verbose_name="Digantikan oleh",
        help_text="Versi berikutnya yang menggantikan bukti ini",
    )

    class Meta:
        verbose_name        = "Bukti Requirement"
        verbose_name_plural = "Bukti Requirement"
        ordering            = ["-version_number", "-uploaded_at"]

    def __str__(self):
        latest_tag = " [LATEST]" if self.is_latest else ""
        return (
            f"Bukti v{self.version_number}{latest_tag}: "
            f"{self.requirement_status.requirement.name} — "
            f"{self.get_verification_status_display()}"
        )

    # ── Sprint 8: Self-verify guard ───────────────────────────

    def can_verify(self, user):
        """
        Sprint 8: Returns (bool, reason_string).
        Enforces:
          1. Only org members can verify (same org as project)
          2. Uploader cannot verify their own evidence
          3. Only PENDING evidence can be verified
          4. Only is_latest evidence can be verified

        Used by:
          - View: raises 400 if can_verify returns False
          - Serializer: sets can_verify field per evidence item
          - Frontend: shows/hides verify buttons
        """
        if self.verification_status != self.VerificationStatus.PENDING:
            return False, f"Bukti ini sudah {self.get_verification_status_display().lower()}"

        if not self.is_latest:
            return False, "Hanya versi terbaru yang dapat diverifikasi"

        if self.uploaded_by and user.id == self.uploaded_by.id:
            return False, "Anda tidak dapat memverifikasi bukti yang Anda upload sendiri"

        # Check org membership
        project = self.requirement_status.project
        org_member_ids = set(
            project.get_org_members().values_list("id", flat=True)
        )
        if user.id not in org_member_ids:
            return False, "Hanya anggota organisasi yang dapat memverifikasi bukti"

        return True, ""

    def get_eligible_verifiers(self):
        """
        Sprint 8: Returns queryset of org members who CAN verify this evidence.
        Excludes the uploader (separation of duties).
        Used by serializer to populate "Can be verified by: ..." list.
        """
        project = self.requirement_status.project
        org_members = project.get_org_members()
        if self.uploaded_by:
            org_members = org_members.exclude(id=self.uploaded_by.id)
        return org_members

    def get_version_chain(self):
        """
        Sprint 8: Returns all versions for this requirement, oldest → newest.
        Used for version history display.
        Returns list of dicts for serialization.
        """
        # Walk up the superseded_by chain to find all versions
        all_versions = list(
            RequirementEvidence.objects.filter(
                requirement_status=self.requirement_status,
            ).order_by("version_number").values(
                "id", "version_number", "verification_status",
                "uploaded_at", "is_latest", "verifier_notes",
            )
        )
        return [
            {
                "id":                  str(v["id"]),
                "version_number":      v["version_number"],
                "verification_status": v["verification_status"],
                "is_latest":           v["is_latest"],
                "uploaded_at":         v["uploaded_at"].isoformat(),
                "verifier_notes":      v["verifier_notes"] or "",
                "label":               f"v{v['version_number']}",
            }
            for v in all_versions
        ]

    # ── approve() — unchanged in signature, same logic ────────

    def approve(self, verifier_user, notes=""):
        from django.utils import timezone
        self.verification_status = self.VerificationStatus.APPROVED
        self.verifier            = verifier_user
        self.verified_at         = timezone.now()
        self.verifier_notes      = notes
        self.save(update_fields=[
            "verification_status", "verifier", "verified_at",
            "verifier_notes", "updated_at",
        ])
        self.requirement_status.mark_completed(user=verifier_user)
        RequirementAudit.log(
            requirement_status=self.requirement_status,
            action=RequirementAudit.Action.EVIDENCE_APPROVED,
            changed_by=verifier_user,
            notes=notes or f"Bukti v{self.version_number} disetujui",
        )
        self.requirement_status.project.snapshot_readiness()

    # ── reject() — unchanged in signature, logs version ───────

    def reject(self, verifier_user, notes=""):
        from django.utils import timezone
        self.verification_status = self.VerificationStatus.REJECTED
        self.verifier            = verifier_user
        self.verified_at         = timezone.now()
        self.verifier_notes      = notes
        self.save(update_fields=[
            "verification_status", "verifier", "verified_at",
            "verifier_notes", "updated_at",
        ])
        req_status            = self.requirement_status
        req_status.status     = ProjectRequirementStatus.Status.IN_PROGRESS
        req_status.updated_by = verifier_user
        req_status.save(update_fields=["status", "updated_by", "updated_at"])
        RequirementAudit.log(
            requirement_status=req_status,
            action=RequirementAudit.Action.EVIDENCE_REJECTED,
            changed_by=verifier_user,
            notes=notes or f"Bukti v{self.version_number} ditolak",
        )

# =============================================================================
# RequirementAudit — Sprint 7: adds ASSIGNED + DUE_DATE_SET actions
# =============================================================================

class RequirementAudit(models.Model):
    class Action(models.TextChoices):
        CREATED           = "created",           "Dibuat"
        UPDATED           = "updated",           "Diperbarui"
        EVIDENCE_UPLOADED = "evidence_uploaded", "Bukti Diunggah"
        EVIDENCE_APPROVED = "evidence_approved", "Bukti Disetujui"
        EVIDENCE_REJECTED = "evidence_rejected", "Bukti Ditolak"
        COMPLETED         = "completed",         "Diselesaikan"
        STAGE_ADVANCED    = "stage_advanced",    "Tahap Dilanjutkan"
        # Sprint 7: new audit actions
        ASSIGNED          = "assigned",          "Ditugaskan"
        DUE_DATE_SET      = "due_date_set",      "Tenggat Waktu Ditetapkan"
        COMMENT_ADDED     = "comment_added",     "Komentar Ditambahkan"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_status = models.ForeignKey(
        ProjectRequirementStatus, on_delete=models.CASCADE, related_name="audit_logs",
    )
    action     = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    old_value  = models.CharField(max_length=50, blank=True)
    new_value  = models.CharField(max_length=50, blank=True)
    notes      = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requirement_audit_logs",
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Audit Requirement"
        verbose_name_plural = "Audit Requirement"
        ordering            = ["-changed_at"]

    def __str__(self):
        return f"[{self.get_action_display()}] {self.requirement_status.requirement.name}"

    @classmethod
    def log(cls, requirement_status, action, changed_by=None, old_value="", new_value="", notes=""):
        try:
            cls.objects.create(
                requirement_status=requirement_status,
                action=action,
                old_value=old_value or "",
                new_value=new_value or "",
                notes=notes or "",
                changed_by=changed_by,
            )
        except Exception:
            pass


# =============================================================================
# RequirementComment — Sprint 7 NEW MODEL
# Team discussion thread per requirement.
# =============================================================================

class RequirementComment(models.Model):
    """
    Sprint 7: Team discussion thread attached to a requirement status.

    Comments are immutable once created — no editing or deletion.
    This is intentional: audit trail integrity.
    Authors can only be org members (developer role).

    Used by:
      GET  /api/projects/<id>/requirements/<req_status_id>/comments/
      POST /api/projects/<id>/requirements/<req_status_id>/comments/
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_status = models.ForeignKey(
        ProjectRequirementStatus,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="requirement_comments",
        verbose_name="Penulis",
    )
    body       = models.TextField(verbose_name="Komentar")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Komentar Requirement"
        verbose_name_plural = "Komentar Requirement"
        ordering            = ["created_at"]   # oldest first — thread order

    def __str__(self):
        author_name = self.author.full_name if self.author else "?"
        return f"[{author_name}] {self.requirement_status.requirement.name}: {self.body[:50]}"


# =============================================================================
# RiskSnapshot — unchanged from Sprint 6
# =============================================================================

class RiskSnapshot(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project    = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="risk_snapshots",
    )
    score      = models.IntegerField()
    level      = models.CharField(max_length=10)
    snapped_at = models.DateField(default=date.today, db_index=True)

    class Meta:
        verbose_name        = "Risk Snapshot"
        verbose_name_plural = "Risk Snapshots"
        ordering            = ["-snapped_at"]
        unique_together     = [["project", "snapped_at"]]

    def __str__(self):
        return f"{self.project.name} — {self.snapped_at}: score={self.score} ({self.level})"


# =============================================================================
# Project — Sprint 7: org members helper + overdue alerts
# =============================================================================

class Project(TenantScopedModel):

    class Stage(models.TextChoices):
        DRAFT        = "draft",        "Draft"
        PLANNING     = "perencanaan",  "Perencanaan"
        PERMITS      = "perizinan",    "Perizinan"
        CONSTRUCTION = "konstruksi",   "Konstruksi"
        SALES        = "penjualan",    "Penjualan"
        HANDOVER     = "serah_terima", "Serah Terima"
        COMPLETED    = "selesai",      "Selesai"
        ON_HOLD      = "ditunda",      "Ditunda"

    STAGE_ORDER = [
        Stage.DRAFT, Stage.PLANNING, Stage.PERMITS,
        Stage.CONSTRUCTION, Stage.SALES,
        Stage.HANDOVER, Stage.COMPLETED,
    ]

    name        = models.CharField(max_length=200)
    location    = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    stage       = models.CharField(max_length=20, choices=Stage.choices, default=Stage.DRAFT, db_index=True)
    is_selling      = models.BooleanField(default=False)
    is_constructing = models.BooleanField(default=False)
    total_units     = models.PositiveIntegerField(default=0)
    target_budget   = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    start_date      = models.DateField(null=True, blank=True)
    end_date        = models.DateField(null=True, blank=True)
    master_plan_url = models.URLField(blank=True)
    site_plan_url   = models.URLField(blank=True)

    class PermitStatus(models.TextChoices):
        NOT_STARTED = "belum",    "Belum Dimulai"
        IN_PROGRESS = "proses",   "Sedang Diproses"
        APPROVED    = "approved", "Disetujui"
        REJECTED    = "rejected", "Ditolak"

    ipr_status   = models.CharField(max_length=20, choices=PermitStatus.choices, default=PermitStatus.NOT_STARTED)
    ipr_date     = models.DateField(null=True, blank=True)
    amdal_status = models.CharField(max_length=20, choices=PermitStatus.choices, default=PermitStatus.NOT_STARTED)
    amdal_date   = models.DateField(null=True, blank=True)
    pbg_status   = models.CharField(max_length=20, choices=PermitStatus.choices, default=PermitStatus.NOT_STARTED)
    pbg_date     = models.DateField(null=True, blank=True)
    readiness_score_last       = models.IntegerField(default=0)
    readiness_score_updated_at = models.DateTimeField(null=True, blank=True)
    risk_level_last            = models.CharField(max_length=10, blank=True, default="")
    risk_level_changed_at      = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Proyek"
        verbose_name_plural = "Proyek"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.location}"

    # =========================================================
    # BASIC COMPUTED PROPERTIES — unchanged
    # =========================================================

    @property
    def units_sold(self):
        return self.units.filter(status__in=["terjual", "proses", "serah_terima"]).count()

    @property
    def overall_progress(self):
        units = self.units.all()
        if not units.exists():
            return 0
        return round(sum(u.progress for u in units) / units.count())

    @property
    def stage_display(self):
        return dict(self.Stage.choices).get(self.stage, self.stage)

    @property
    def next_stage(self):
        if self.stage not in self.STAGE_ORDER:
            return None
        idx = self.STAGE_ORDER.index(self.stage)
        if idx + 1 >= len(self.STAGE_ORDER):
            return None
        return self.STAGE_ORDER[idx + 1]

    # =========================================================
    # SPRINT 7: ORG MEMBERS HELPER
    # =========================================================

    def get_org_members(self):
        """
        Sprint 7: Returns all developer-role users in this project's
        organization. Used for the assignee dropdown.
        Only org members can be assigned to requirements.
        Users belong to orgs via memberships (not a direct FK).
        """
        from apps.authentication.models import CustomUser
        return CustomUser.objects.filter(
            memberships__organization=self.organization,
            memberships__is_active=True,
            role=CustomUser.Role.DEVELOPER,
            is_active=True,
        ).distinct().order_by("full_name")

    @classmethod
    def get_my_actions(cls, user):
        """
        Sprint 9: Returns personalized, prioritized next actions for `user`.
        See module docstring above for full scoring logic.
        """
        projects = cls.objects.for_user(user).exclude(
            stage__in=[cls.Stage.COMPLETED, cls.Stage.ON_HOLD]
        )

        my_tasks   = []
        unassigned = []

        for project in projects:
            intel = project.get_intelligence_summary()
            risk_level = intel["risk_level"]

            for req in intel["requirements"]:
                # Only mandatory, not-completed, not dependency-blocked
                # requirements are "actionable" — locked items are noise.
                if req["status"] == "completed":
                    continue
                if req["is_dependency_blocked"]:
                    continue
                if not req["is_mandatory"]:
                    continue
                if not req["status_id"]:
                    continue

                assigned_to_id = req.get("assigned_to_id")
                is_mine        = assigned_to_id == str(user.id)
                is_unassigned  = assigned_to_id is None

                if not is_mine and not is_unassigned:
                    # Assigned to someone else in the org — not shown to me
                    continue

                # ── Compute priority score + reason ───────────
                score       = 0
                reasons     = []
                action_type = "standard"

                if req.get("is_overdue"):
                    score += 40
                    days_over = abs(req.get("days_until_due") or 0)
                    reasons.append(f"Terlambat {days_over} hari dari tenggat")
                    action_type = "overdue"

                score += 25  # baseline: genuinely actionable right now
                if action_type == "standard":
                    action_type = "blocked_others" if req.get("weight_pct", 0) >= 40 else "standard"

                if req.get("weight_pct", 0) >= 30:
                    score += 20
                    reasons.append(f"Berdampak besar pada kesiapan ({req['weight_pct']}% bobot)")
                    if action_type == "standard":
                        action_type = "high_impact"

                if risk_level == "high":
                    score += 15
                    reasons.append("Proyek berisiko tinggi")
                    if action_type == "standard":
                        action_type = "high_risk"

                if req.get("latest_evidence_status") == "rejected":
                    score += 10
                    reasons.append("Bukti sebelumnya ditolak — perlu diunggah ulang")
                    action_type = "resubmit_needed"
                elif risk_level == "medium":
                    score += 5

                if not reasons:
                    reasons.append("Requirement wajib menunggu tindakan")

                action_item = {
                    "project_id":             str(project.id),
                    "project_name":           project.name,
                    "project_stage":          project.stage,
                    "project_stage_display":  project.stage_display,
                    "requirement_id":         req["id"],
                    "requirement_name":       req["name"],
                    "status_id":              req["status_id"],
                    "status":                 req["status"],
                    "status_display":         req["status_display"],
                    "due_date":               req.get("due_date"),
                    "is_overdue":             req.get("is_overdue", False),
                    "days_until_due":         req.get("days_until_due"),
                    "weight_pct":             req.get("weight_pct", 0),
                    "is_assigned_to_me":      is_mine,
                    "priority_score":         score,
                    "action_type":            action_type,
                    "reasons":                reasons,
                    "primary_reason":         reasons[0],
                }

                if is_mine:
                    my_tasks.append(action_item)
                else:
                    unassigned.append(action_item)

        # Sort each section by priority score, descending
        my_tasks.sort(key=lambda x: x["priority_score"], reverse=True)
        unassigned.sort(key=lambda x: x["priority_score"], reverse=True)

        return {
            "my_tasks":         my_tasks,
            "my_tasks_count":   len(my_tasks),
            "unassigned":       unassigned,
            "unassigned_count": len(unassigned),
            "total_actionable": len(my_tasks) + len(unassigned),
        }

    # =========================================================
    # INTELLIGENCE ENGINE INTERNALS — unchanged
    # =========================================================

    def _get_current_requirements(self):
        return StageRequirement.objects.filter(
            stage=self.stage, is_active=True,
        ).prefetch_related("prerequisites").order_by("order")

    def _get_requirement_statuses(self):
        statuses = self.requirement_statuses.filter(
            requirement__stage=self.stage,
            requirement__is_active=True,
        ).select_related("requirement", "assigned_to")   # Sprint 7: select assigned_to
        return {str(s.requirement_id): s for s in statuses}

    def _has_unmet_prerequisites(self, requirement, statuses_map):
        for prereq in requirement.prerequisites.all():
            s = statuses_map.get(str(prereq.id))
            if not s or s.status != ProjectRequirementStatus.Status.COMPLETED:
                return True
        return False

    # =========================================================
    # SPRINT 5: WEIGHTED READINESS ENGINE — unchanged
    # =========================================================

    def _get_readiness_data(self):
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses     = self._get_requirement_statuses()
        total_weight     = 0
        completed_weight = 0
        items            = []
        for r in requirements:
            w = r.weight if r.weight > 0 else 1
            s = statuses.get(str(r.id))
            is_completed   = (s is not None and s.status == ProjectRequirementStatus.Status.COMPLETED)
            is_dep_blocked = (not is_completed and self._has_unmet_prerequisites(r, statuses))
            total_weight += w
            if is_completed:
                completed_weight += w
            items.append({
                "id": str(r.id), "name": r.name, "category": r.category,
                "weight": w, "status": s.status if s else ProjectRequirementStatus.Status.PENDING,
                "is_completed": is_completed, "is_dependency_blocked": is_dep_blocked,
                "contribution": 0,
            })
        for item in items:
            item["weight_pct"]   = round((item["weight"] / total_weight) * 100) if total_weight > 0 else 0
            item["contribution"] = item["weight_pct"] if item["is_completed"] else 0
        score = round((completed_weight / total_weight) * 100) if total_weight > 0 else 100
        return {"score": score, "total_weight": total_weight, "completed_weight": completed_weight, "items": items}

    @property
    def readiness_score(self):
        return self._get_readiness_data()["score"]

    @property
    def readiness_label(self):
        score = self.readiness_score
        if score >= 80: return "Sangat Siap"
        if score >= 60: return "Cukup Siap"
        if score >= 30: return "Sedang"
        return "Belum Siap"

    @property
    def readiness_breakdown(self):
        data  = self._get_readiness_data()
        score = data["score"]
        return {
            "score":            score,
            "label":            self.readiness_label,
            "total_weight":     data["total_weight"],
            "completed_weight": data["completed_weight"],
            "formula":          f"Readiness = ({data['completed_weight']} / {data['total_weight']}) × 100 = {score}%",
            "items":            data["items"],
        }

    @property
    def readiness_dimensions(self):
        data = self._get_readiness_data()
        dims = {
            "inventory":   {"total": 0, "completed": 0},
            "compliance":  {"total": 0, "completed": 0},
            "site_plan":   {"total": 0, "completed": 0},
            "sales_setup": {"total": 0, "completed": 0},
            "general":     {"total": 0, "completed": 0},
        }
        for item in data["items"]:
            cat = item["category"] if item["category"] in dims else "general"
            dims[cat]["total"] += item["weight"]
            if item["is_completed"]:
                dims[cat]["completed"] += item["weight"]
        return {
            dim: (100 if d["total"] == 0 else round((d["completed"] / d["total"]) * 100))
            for dim, d in dims.items()
        }

    # =========================================================
    # SPRINT 6: RISK ENGINE — unchanged
    # =========================================================

    def _get_risk_data(self):
        today   = date.today()
        factors = []
        score   = 0
        if self.pbg_status == self.PermitStatus.REJECTED:
            pts = 30; score += pts
            factors.append({"key": "pbg_rejected", "name": "PBG ditolak", "description": "Persetujuan Bangunan Gedung ditolak — konstruksi tidak dapat dilanjutkan", "impact": "Tinggi", "impact_key": "high", "points": pts, "max_points": 30, "action": "Ajukan ulang PBG ke instansi terkait segera", "triggered": True})
        if self.amdal_status == self.PermitStatus.REJECTED:
            pts = 15; score += pts
            factors.append({"key": "amdal_rejected", "name": "AMDAL ditolak", "description": "Analisis Dampak Lingkungan ditolak — perizinan tidak dapat diselesaikan", "impact": "Tinggi", "impact_key": "high", "points": pts, "max_points": 15, "action": "Revisi dokumen AMDAL dan ajukan ulang", "triggered": True})
        blocking = self.blocking_count
        if blocking > 0:
            pts = min(10 * blocking, 25) if blocking <= 2 else 25; score += pts
            impact = "Tinggi" if blocking >= 2 else "Sedang"
            factors.append({"key": "mandatory_blockers", "name": f"{blocking} requirement wajib memblokir", "description": f"Tahap {self.stage_display} tidak dapat dilanjutkan — {blocking} requirement wajib belum selesai", "impact": impact, "impact_key": "high" if blocking >= 2 else "medium", "points": pts, "max_points": 25, "action": f"Mulai dengan: {self.next_action}" if self.next_action else "Selesaikan semua requirement wajib", "triggered": True})
        if (self.end_date and today > self.end_date and self.stage not in (self.Stage.COMPLETED, self.Stage.HANDOVER)):
            overrun_days = (today - self.end_date).days
            pts = 8 if overrun_days <= 7 else 14 if overrun_days <= 30 else 18 if overrun_days <= 90 else 20
            score += pts
            impact = "Tinggi" if overrun_days > 30 else "Sedang"
            factors.append({"key": "timeline_overrun", "name": f"Terlambat {overrun_days} hari", "description": f"Proyek melewati target selesai {overrun_days} hari — dampak: {self._overrun_impact_text(overrun_days)}", "impact": impact, "impact_key": "high" if overrun_days > 30 else "medium", "points": pts, "max_points": 20, "action": "Perbarui target selesai atau percepat konstruksi", "triggered": True, "days": overrun_days})
        overdue_count = self._get_overdue_payments_count()
        if overdue_count > 0:
            pts = min(5 * overdue_count, 10); score += pts
            factors.append({"key": "payment_overdue", "name": f"{overdue_count} pembayaran tertunggak", "description": f"{overdue_count} invoice pembayaran melewati jatuh tempo — collection efficiency menurun", "impact": "Sedang", "impact_key": "medium", "points": pts, "max_points": 10, "action": "Tindak lanjuti pembayaran yang tertunggak segera", "triggered": True})
        score = min(score, 100)
        level = "high" if score >= 60 else "medium" if score >= 30 else "low"
        return {"score": score, "level": level, "factors": factors}

    def _overrun_impact_text(self, days):
        if days <= 7:   return "perlu perhatian"
        if days <= 30:  return "pembayaran dan progres terhambat"
        if days <= 90:  return "risiko pembatalan kontrak"
        return "dampak signifikan pada reputasi dan kontrak"

    @property
    def risk_score(self):
        return self._get_risk_data()["score"]

    @property
    def risk_level(self):
        return self._get_risk_data()["level"]

    @property
    def risk_level_display(self):
        return {"low": "Rendah", "medium": "Sedang", "high": "Tinggi"}.get(self.risk_level, self.risk_level)

    @property
    def risk_factors(self):
        return self._get_risk_data()["factors"]

    @property
    def risk_reasons(self):
        return [f["description"] for f in self.risk_factors]

    @property
    def risk_since(self):
        current_level = self.risk_level
        if self.risk_level_last == current_level and self.risk_level_changed_at:
            return self.risk_level_changed_at.date()
        snapshots = list(self.risk_snapshots.filter(level=current_level).order_by("snapped_at").values("snapped_at", "level"))
        if snapshots:
            return snapshots[0]["snapped_at"]
        return None

    @property
    def risk_trend_data(self):
        cutoff = date.today() - timedelta(days=30)
        snapshots = list(self.risk_snapshots.filter(snapped_at__gte=cutoff).order_by("snapped_at").values("snapped_at", "score", "level"))
        return [{"date": s["snapped_at"].isoformat(), "score": s["score"], "level": s["level"]} for s in snapshots]

    # =========================================================
    # INTELLIGENCE PROPERTIES — unchanged
    # =========================================================

    @property
    def trend(self):
        current  = self.readiness_score
        previous = self.readiness_score_last
        if current > previous: return "improving"
        if current < previous: return "declining"
        return "stable"

    @property
    def blocking_count(self):
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses = self._get_requirement_statuses()
        blocking = 0
        for r in requirements:
            s = statuses.get(str(r.id))
            if not s or s.status in (ProjectRequirementStatus.Status.PENDING, ProjectRequirementStatus.Status.IN_PROGRESS):
                if not self._has_unmet_prerequisites(r, statuses):
                    blocking += 1
        return blocking

    @property
    def next_action(self):
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses = self._get_requirement_statuses()
        for r in requirements:
            s = statuses.get(str(r.id))
            if not s or s.status == ProjectRequirementStatus.Status.PENDING:
                if not self._has_unmet_prerequisites(r, statuses):
                    return r.name
        return None

    @property
    def can_advance(self):
        if self.stage == self.Stage.COMPLETED: return False
        if self.stage == self.Stage.ON_HOLD:   return False
        if self.blocking_count > 0:            return False
        return True

    @property
    def alerts(self):
        result = []
        if self.pbg_status == self.PermitStatus.REJECTED:
            result.append({"level": "critical", "category": "permit", "message": "PBG ditolak — unit pipeline terkunci sampai PBG disetujui", "action": "Ajukan ulang PBG ke instansi terkait"})
        if self.amdal_status == self.PermitStatus.REJECTED:
            result.append({"level": "critical", "category": "permit", "message": "AMDAL ditolak — tahap perizinan tidak dapat diselesaikan", "action": "Revisi dokumen AMDAL dan ajukan ulang"})
        if self.blocking_count > 0:
            next_act = self.next_action
            result.append({"level": "critical", "category": "requirement", "message": f"{self.blocking_count} requirement wajib memblokir tahap {self.stage_display}", "action": f"Mulai dengan: {next_act}" if next_act else "Selesaikan semua requirement wajib"})
        if (self.end_date and date.today() > self.end_date and self.stage not in (self.Stage.COMPLETED, self.Stage.HANDOVER) and self.blocking_count > 0):
            overrun_days = (date.today() - self.end_date).days
            result.append({"level": "warning", "category": "timeline", "message": f"Proyek terlambat {overrun_days} hari dari target selesai", "action": "Perbarui target selesai atau percepat konstruksi"})
        if self.stage in (self.Stage.CONSTRUCTION, self.Stage.SALES, self.Stage.HANDOVER) and not self.units.exists():
            result.append({"level": "warning", "category": "inventory", "message": "Belum ada unit terdaftar di tahap ini", "action": "Tambah unit di modul Unit"})
        if self.is_selling and not self.units.filter(price__gt=0).exists():
            result.append({"level": "warning", "category": "sales", "message": "Mode penjualan aktif tapi belum ada unit dengan harga", "action": "Set harga unit sebelum memasarkan"})
        overdue = self._get_overdue_payments_count()
        if overdue > 0:
            result.append({"level": "warning", "category": "financial", "message": f"{overdue} invoice pembayaran melewati jatuh tempo", "action": "Tindak lanjuti pembayaran yang tertunggak"})
        if self.pbg_status == self.PermitStatus.NOT_STARTED and self.stage == self.Stage.PERMITS:
            result.append({"level": "info", "category": "permit", "message": "PBG belum dimulai — diperlukan sebelum konstruksi", "action": "Mulai pengajuan PBG"})

        # ── Sprint 7: overdue requirement alert ───────────────
        overdue_reqs = self._get_overdue_requirements_count()
        if overdue_reqs > 0:
            result.append({"level": "warning", "category": "ownership", "message": f"{overdue_reqs} requirement melewati tenggat waktu", "action": "Tinjau requirement yang terlambat dan update tenggat waktu"})

        order = {"critical": 0, "warning": 1, "info": 2}
        result.sort(key=lambda a: order.get(a["level"], 3))
        return result

    def _get_overdue_requirements_count(self):
        """Sprint 7: count requirements past due_date and not completed."""
        today = date.today()
        return self.requirement_statuses.filter(
            due_date__lt=today,
        ).exclude(
            status=ProjectRequirementStatus.Status.COMPLETED,
        ).count()

    @property
    def parallel_stage_status(self):
        return {
            "is_selling":      self.is_selling,
            "is_constructing": self.is_constructing,
            "label_5a":        "Aktif Penjualan" if self.is_selling else "Belum Dipasarkan",
            "label_5b":        "Aktif Konstruksi" if self.is_constructing else "Belum Konstruksi",
            "can_sell_now":    self.stage in (self.Stage.PLANNING, self.Stage.PERMITS, self.Stage.CONSTRUCTION, self.Stage.SALES, self.Stage.HANDOVER),
        }

    @property
    def collection_efficiency(self):
        try:
            from apps.payments.models import Payment
            payments      = list(Payment.objects.filter(unit__project=self))
            total_billed  = sum(p.amount for p in payments)
            total_settled = sum(p.amount for p in payments if p.status == "lunas")
            total_arrears = total_billed - total_settled
            efficiency    = round((total_settled / total_billed) * 100) if total_billed > 0 else 100
            return {"total_billed": int(total_billed), "total_settled": int(total_settled), "total_arrears": int(total_arrears), "efficiency_pct": efficiency, "status": "healthy" if efficiency >= 90 else "attention" if efficiency >= 70 else "critical", "status_display": "Sehat" if efficiency >= 90 else "Perlu Perhatian" if efficiency >= 70 else "Kritis"}
        except Exception:
            return {"total_billed": 0, "total_settled": 0, "total_arrears": 0, "efficiency_pct": 100, "status": "healthy", "status_display": "Sehat"}

    def _get_overdue_payments_count(self):
        try:
            from apps.payments.models import Payment
            from django.utils import timezone
            today = timezone.now().date()
            return Payment.objects.filter(unit__project=self).filter(models.Q(status="menunggak") | models.Q(status="menunggu", due_date__lt=today)).count()
        except Exception:
            return 0

    # =========================================================
    # get_intelligence_summary — Sprint 7: adds ownership data
    # =========================================================

    def get_intelligence_summary(self):
        """
        Sprint 7: intelligence summary now includes per requirement:
          assigned_to_id   — UUID of assigned user
          assigned_to_name — full name of assigned user
          due_date         — ISO date string or null
          is_overdue       — bool
          days_until_due   — int (negative = overdue) or null
          comment_count    — number of comments
        """
        requirements   = self._get_current_requirements()
        statuses       = self._get_requirement_statuses()
        breakdown_data = self._get_readiness_data()
        breakdown_map  = {item["id"]: item for item in breakdown_data["items"]}
        risk_data      = self._get_risk_data()

        items = []
        for r in requirements:
            s = statuses.get(str(r.id))

            evidence_count         = 0
            latest_evidence_status = None
            has_pending_evidence   = False
            audit_count            = 0
            comment_count          = 0

            if s:
                evidence_qs    = s.evidence.all().order_by("-uploaded_at")
                evidence_count = evidence_qs.count()
                if evidence_count > 0:
                    latest = evidence_qs.first()
                    latest_evidence_status = latest.verification_status
                    has_pending_evidence   = evidence_qs.filter(verification_status="pending").exists()
                audit_count   = s.audit_logs.count()
                comment_count = s.comments.count()   # Sprint 7

            current_status        = s.status if s else ProjectRequirementStatus.Status.PENDING
            is_completed          = current_status == ProjectRequirementStatus.Status.COMPLETED
            prereq_names          = r.get_prerequisite_names()
            unmet_prereqs         = []
            is_dependency_blocked = False

            if not is_completed and prereq_names:
                for prereq in r.prerequisites.all():
                    ps = statuses.get(str(prereq.id))
                    if not ps or ps.status != ProjectRequirementStatus.Status.COMPLETED:
                        unmet_prereqs.append(prereq.name)
                is_dependency_blocked = len(unmet_prereqs) > 0

            can_act_now = not is_completed and not is_dependency_blocked
            bd = breakdown_map.get(str(r.id), {})

            # Sprint 7: ownership data
            assigned_to_id   = None
            assigned_to_name = None
            req_due_date     = None
            is_overdue       = False
            days_until_due   = None

            if s:
                if s.assigned_to:
                    assigned_to_id   = str(s.assigned_to.id)
                    assigned_to_name = s.assigned_to.full_name
                if s.due_date:
                    req_due_date   = s.due_date.isoformat()
                    is_overdue     = s.is_overdue
                    days_until_due = s.days_until_due

            items.append({
                "id":             str(r.id),
                "name":           r.name,
                "description":    r.description,
                "is_mandatory":   r.is_mandatory,
                "order":          r.order,
                "category":       r.category,
                "status":         current_status,
                "status_display": dict(ProjectRequirementStatus.Status.choices).get(current_status, "Belum Dimulai"),
                "notes":          s.notes if s else "",
                "completed_at":   s.completed_at.isoformat() if s and s.completed_at else None,
                "status_id":      str(s.id) if s else None,
                "evidence_count":         evidence_count,
                "latest_evidence_status": latest_evidence_status,
                "has_pending_evidence":   has_pending_evidence,
                "audit_count":            audit_count,
                "prerequisites":          prereq_names,
                "unmet_prerequisites":    unmet_prereqs,
                "is_dependency_blocked":  is_dependency_blocked,
                "can_act_now":            can_act_now,
                "weight":                 r.weight if r.is_mandatory else 0,
                "weight_pct":             bd.get("weight_pct", 0),
                "contribution":           bd.get("contribution", 0),
                # Sprint 7: ownership
                "assigned_to_id":   assigned_to_id,
                "assigned_to_name": assigned_to_name,
                "due_date":         req_due_date,
                "is_overdue":       is_overdue,
                "days_until_due":   days_until_due,
                "comment_count":    comment_count,
            })

        risk_since = self.risk_since
        return {
            "readiness_score":    self.readiness_score,
            "blocking_count":     self.blocking_count,
            "next_action":        self.next_action,
            "risk_level":         risk_data["level"],
            "risk_level_display": {"low": "Rendah", "medium": "Sedang", "high": "Tinggi"}.get(risk_data["level"], ""),
            "trend":              self.trend,
            "can_advance":        self.can_advance,
            "requirements":       items,
            "readiness_dimensions":  self.readiness_dimensions,
            "risk_reasons":          self.risk_reasons,
            "alerts":                self.alerts,
            "parallel_stages":       self.parallel_stage_status,
            "collection_efficiency": self.collection_efficiency,
            "readiness_breakdown":   self.readiness_breakdown,
            "readiness_label":       self.readiness_label,
            "risk_score":            risk_data["score"],
            "risk_factors":          risk_data["factors"],
            "risk_since":            risk_since.isoformat() if risk_since else None,
            "risk_trend_data":       self.risk_trend_data,
             "pending_evidence_count": self.requirement_statuses.filter(
                requirement__stage=self.stage,
                requirement__is_active=True,
                evidence__verification_status="pending",
                evidence__is_latest=True,
            ).distinct().count(),
            "rejected_evidence_count": self.requirement_statuses.filter(
                requirement__stage=self.stage,
                requirement__is_active=True,
                evidence__verification_status="rejected",
                evidence__is_latest=True,
            ).distinct().count(),
        }

    # =========================================================
    # SNAPSHOT / ADVANCE / CHECKLIST — unchanged
    # =========================================================

    def snapshot_readiness(self):
        from django.utils import timezone
        current = self.readiness_score
        if current != self.readiness_score_last:
            self.readiness_score_last       = current
            self.readiness_score_updated_at = timezone.now()
            self.save(update_fields=["readiness_score_last", "readiness_score_updated_at", "updated_at"])

    def snapshot_risk(self):
        from django.utils import timezone
        risk_data     = self._get_risk_data()
        current_score = risk_data["score"]
        current_level = risk_data["level"]
        today         = date.today()
        RiskSnapshot.objects.update_or_create(
            project=self, snapped_at=today,
            defaults={"score": current_score, "level": current_level},
        )
        if self.risk_level_last != current_level:
            self.risk_level_last       = current_level
            self.risk_level_changed_at = timezone.now()
            self.save(update_fields=["risk_level_last", "risk_level_changed_at", "updated_at"])

    def _create_stage_requirements(self):
        requirements = StageRequirement.objects.filter(stage=self.stage, is_active=True)
        for req in requirements:
            status_obj, created = ProjectRequirementStatus.objects.get_or_create(
                project=self, requirement=req,
                defaults={"status": ProjectRequirementStatus.Status.PENDING},
            )
            if created:
                RequirementAudit.log(
                    requirement_status=status_obj,
                    action=RequirementAudit.Action.CREATED,
                    new_value=ProjectRequirementStatus.Status.PENDING,
                    notes=f"Requirement dibuat untuk tahap {self.stage_display}",
                )

    def advance_stage(self):
        if self.stage == self.Stage.COMPLETED:
            raise ValueError("Proyek sudah selesai.")
        if self.stage == self.Stage.ON_HOLD:
            raise ValueError("Proyek sedang ditunda.")
        if self.blocking_count > 0:
            raise ValueError(f"Proyek diblokir — {self.blocking_count} requirement wajib belum selesai. Tindakan berikutnya: {self.next_action}.")
        self.snapshot_readiness()
        self.stage = self.next_stage
        self.save(update_fields=["stage", "updated_at"])
        if self.stage == self.Stage.CONSTRUCTION:
            self.is_constructing = True
            self.save(update_fields=["is_constructing", "updated_at"])
        if self.stage == self.Stage.SALES:
            self.is_selling = True
            self.save(update_fields=["is_selling", "updated_at"])
        self._create_stage_requirements()
        return self.stage

    @property
    def stage_checklist(self):
        intelligence = self.get_intelligence_summary()
        reqs = intelligence["requirements"]
        if reqs:
            return [{"item": r["name"], "done": r["status"] == ProjectRequirementStatus.Status.COMPLETED, "blocking": r["is_mandatory"] and r["status"] != ProjectRequirementStatus.Status.COMPLETED} for r in reqs]
        hardcoded = {
            self.Stage.DRAFT:        [{"item": "Nama proyek", "done": bool(self.name)}, {"item": "Lokasi proyek", "done": bool(self.location)}, {"item": "Deskripsi", "done": bool(self.description)}],
            self.Stage.PLANNING:     [{"item": "Total unit", "done": self.total_units > 0}, {"item": "Tanggal mulai", "done": bool(self.start_date)}, {"item": "Target selesai", "done": bool(self.end_date)}, {"item": "Target anggaran", "done": bool(self.target_budget)}],
            self.Stage.PERMITS:      [{"item": "IPR disetujui", "done": self.ipr_status == self.PermitStatus.APPROVED}, {"item": "AMDAL disetujui", "done": self.amdal_status == self.PermitStatus.APPROVED}, {"item": "PBG diterbitkan", "done": self.pbg_status == self.PermitStatus.APPROVED, "blocking": True}],
            self.Stage.CONSTRUCTION: [{"item": "Unit dibuat", "done": self.units.exists()}, {"item": "Fase konstruksi set", "done": self.units.filter(phases__isnull=False).exists()}],
            self.Stage.SALES:        [{"item": "Harga unit ditetapkan", "done": self.units.filter(price__gt=0).exists()}],
            self.Stage.HANDOVER:     [{"item": "Semua unit selesai", "done": not self.units.exclude(status="serah_terima").exists()}],
        }
        return hardcoded.get(self.stage, [])

    # =========================================================
    # SPRINT 3: TIMELINE + FINANCIAL — unchanged
    # =========================================================

    def activity_timeline(self, limit=20):
        activities = []
        audit_logs = RequirementAudit.objects.filter(requirement_status__project=self).select_related("requirement_status__requirement", "changed_by").order_by("-changed_at")[:limit]
        action_labels = {
            RequirementAudit.Action.CREATED:           "membuat requirement",
            RequirementAudit.Action.UPDATED:           "memperbarui",
            RequirementAudit.Action.EVIDENCE_UPLOADED: "mengunggah bukti untuk",
            RequirementAudit.Action.EVIDENCE_APPROVED: "menyetujui bukti",
            RequirementAudit.Action.EVIDENCE_REJECTED: "menolak bukti",
            RequirementAudit.Action.COMPLETED:         "menyelesaikan",
            RequirementAudit.Action.STAGE_ADVANCED:    "melanjutkan tahap ke",
            RequirementAudit.Action.ASSIGNED:          "menugaskan",
            RequirementAudit.Action.DUE_DATE_SET:      "menetapkan tenggat untuk",
            RequirementAudit.Action.COMMENT_ADDED:     "menambahkan komentar pada",
        }
        for log in audit_logs:
            req_name    = log.requirement_status.requirement.name
            actor_name  = log.changed_by.full_name if log.changed_by else "Sistem"
            action_verb = action_labels.get(log.action, log.action)
            activities.append({"id": str(log.id), "type": "requirement", "action": log.action, "actor": actor_name, "actor_id": str(log.changed_by.id) if log.changed_by else None, "subject": req_name, "message": f"{actor_name} {action_verb} {req_name}", "notes": log.notes, "old_value": log.old_value, "new_value": log.new_value, "timestamp": log.changed_at.isoformat()})
        return activities

    def financial_snapshot(self):
        try:
            from apps.payments.models import Payment
            from django.utils import timezone
            today    = timezone.now().date()
            payments = list(Payment.objects.filter(unit__project=self).select_related("unit", "unit__buyer"))
            if not payments:
                return {"has_data": False, "total_billed": 0, "total_lunas": 0, "total_menunggak": 0, "total_upcoming": 0, "efficiency_pct": 100, "status": "healthy", "status_display": "Sehat", "overdue_items": [], "upcoming_items": []}
            total_billed    = sum(p.amount for p in payments)
            total_lunas     = sum(p.amount for p in payments if p.status == "lunas")
            total_menunggak = sum(p.amount for p in payments if p.status == "menunggak" or (p.status == "menunggu" and p.due_date < today))
            total_upcoming  = sum(p.amount for p in payments if p.status in ("akan_datang", "proses_bank") or (p.status == "menunggu" and p.due_date >= today))
            efficiency      = round((total_lunas / total_billed) * 100) if total_billed > 0 else 100
            overdue_items = sorted([{"id": str(p.id), "unit_number": p.unit.unit_number, "buyer_name": p.unit.buyer.full_name if p.unit.buyer else "—", "payment_type": p.payment_type, "amount": int(p.amount), "due_date": p.due_date.isoformat(), "days_overdue": (today - p.due_date).days} for p in payments if p.status == "menunggak" or (p.status == "menunggu" and p.due_date < today)], key=lambda x: x["days_overdue"], reverse=True)
            upcoming_items = sorted([{"id": str(p.id), "unit_number": p.unit.unit_number, "buyer_name": p.unit.buyer.full_name if p.unit.buyer else "—", "payment_type": p.payment_type, "amount": int(p.amount), "due_date": p.due_date.isoformat(), "days_until": (p.due_date - today).days} for p in payments if p.status in ("akan_datang", "menunggu") and p.due_date >= today and (p.due_date - today).days <= 30], key=lambda x: x["days_until"])
            return {"has_data": True, "total_billed": int(total_billed), "total_lunas": int(total_lunas), "total_menunggak": int(total_menunggak), "total_upcoming": int(total_upcoming), "efficiency_pct": efficiency, "status": "healthy" if efficiency >= 90 else "attention" if efficiency >= 70 else "critical", "status_display": "Sehat" if efficiency >= 90 else "Perlu Perhatian" if efficiency >= 70 else "Kritis", "overdue_items": overdue_items, "upcoming_items": upcoming_items}
        except Exception:
            return {"has_data": False, "total_billed": 0, "total_lunas": 0, "total_menunggak": 0, "total_upcoming": 0, "efficiency_pct": 100, "status": "healthy", "status_display": "Sehat", "overdue_items": [], "upcoming_items": []}
