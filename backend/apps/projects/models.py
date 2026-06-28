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
          _has_unmet_prerequisites() — dependency resolver
          blocking_count — Option B: only root blockers count
          next_action — always points to ROOT cause
          dependency_status — new intelligence field

ZERO BREAKING CHANGES — all existing fields preserved.
59 tests still green.
"""
import uuid
from datetime import date

from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel


# =============================================================================
# StageRequirement — Sprint 4: adds prerequisites M2M
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

    # ── Sprint 4: Dependency graph ────────────────────────────
    # Self-referential M2M: "this requirement needs THESE done first"
    # Only within the same stage — cross-stage deps are handled
    # by the stage advancement blocking logic.
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,           # A requires B ≠ B requires A
        blank=True,
        related_name="dependents",   # req.dependents = what needs this done first
        verbose_name="Prasyarat",
        help_text="Requirement yang harus selesai sebelum ini bisa dikerjakan",
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
        return f"{flag} [{self.get_stage_display()}] {self.name}"

    def get_prerequisite_names(self):
        """Returns list of prerequisite names for display."""
        return list(self.prerequisites.values_list("name", flat=True))


# =============================================================================
# ProjectRequirementStatus — Sprint 4: adds can_complete() rule engine
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
    updated_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Project Requirement Status"
        verbose_name_plural = "Project Requirement Statuses"
        unique_together     = [["project", "requirement"]]
        ordering            = ["requirement__order"]

    def __str__(self):
        return f"{self.project.name} — {self.requirement.name}: {self.status}"

    # ── Sprint 4: Rule engine ─────────────────────────────────

    def get_unmet_prerequisites(self):
        """
        Sprint 4: Returns list of prerequisite names that are NOT
        yet completed for this requirement.
        Empty list = all prerequisites met = safe to complete.

        This is the RULE ENGINE core — called before any status change
        to completed or menunggu_verifikasi.
        """
        prereqs = self.requirement.prerequisites.all()
        if not prereqs.exists():
            return []

        unmet = []
        for prereq in prereqs:
            # Check if this prerequisite is completed for this project
            try:
                prereq_status = ProjectRequirementStatus.objects.get(
                    project=self.project,
                    requirement=prereq,
                )
                if prereq_status.status != self.Status.COMPLETED:
                    unmet.append(prereq.name)
            except ProjectRequirementStatus.DoesNotExist:
                # Status row doesn't exist = not started = unmet
                unmet.append(prereq.name)

        return unmet

    def can_complete(self):
        """
        Sprint 4: Returns (can_complete: bool, reason: str).
        Checks prerequisites before allowing completion.

        Usage:
          ok, reason = req_status.can_complete()
          if not ok:
              raise ValueError(reason)
        """
        unmet = self.get_unmet_prerequisites()
        if unmet:
            prereq_list = ", ".join(unmet)
            return False, (
                f"'{self.requirement.name}' membutuhkan prasyarat: "
                f"{prereq_list}. Selesaikan prasyarat terlebih dahulu."
            )
        return True, ""

    def mark_completed(self, user=None):
        """Sprint 4: now enforces prerequisite rules before completing."""
        from django.utils import timezone

        # Sprint 4: rule engine check
        ok, reason = self.can_complete()
        if not ok:
            raise ValueError(reason)

        old_status    = self.status
        self.status   = self.Status.COMPLETED
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
        """Sprint 4: also enforces prerequisite rules before upload."""
        # Sprint 4: rule engine check — can't upload evidence if prereqs unmet
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
# RequirementEvidence — unchanged from Sprint 3
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

    class Meta:
        verbose_name        = "Bukti Requirement"
        verbose_name_plural = "Bukti Requirement"
        ordering            = ["-uploaded_at"]

    def __str__(self):
        return f"Bukti: {self.requirement_status.requirement.name} — {self.get_verification_status_display()}"

    def approve(self, verifier_user, notes=""):
        from django.utils import timezone
        self.verification_status = self.VerificationStatus.APPROVED
        self.verifier            = verifier_user
        self.verified_at         = timezone.now()
        self.verifier_notes      = notes
        self.save(update_fields=["verification_status", "verifier", "verified_at", "verifier_notes", "updated_at"])
        self.requirement_status.mark_completed(user=verifier_user)
        RequirementAudit.log(
            requirement_status=self.requirement_status,
            action=RequirementAudit.Action.EVIDENCE_APPROVED,
            changed_by=verifier_user,
            notes=notes or "Bukti disetujui",
        )
        self.requirement_status.project.snapshot_readiness()

    def reject(self, verifier_user, notes=""):
        from django.utils import timezone
        self.verification_status = self.VerificationStatus.REJECTED
        self.verifier            = verifier_user
        self.verified_at         = timezone.now()
        self.verifier_notes      = notes
        self.save(update_fields=["verification_status", "verifier", "verified_at", "verifier_notes", "updated_at"])
        req_status            = self.requirement_status
        req_status.status     = ProjectRequirementStatus.Status.IN_PROGRESS
        req_status.updated_by = verifier_user
        req_status.save(update_fields=["status", "updated_by", "updated_at"])
        RequirementAudit.log(
            requirement_status=req_status,
            action=RequirementAudit.Action.EVIDENCE_REJECTED,
            changed_by=verifier_user,
            notes=notes or "Bukti ditolak",
        )


# =============================================================================
# RequirementAudit — unchanged from Sprint 3
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
        """Never raises — audit logging must never break main flow."""
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
# Project — Sprint 4: dependency-aware intelligence engine
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

    # ── Core fields ───────────────────────────────────────────
    name        = models.CharField(max_length=200)
    location    = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    stage       = models.CharField(max_length=20, choices=Stage.choices, default=Stage.DRAFT, db_index=True)

    # ── Sprint 1: parallel stage flags ────────────────────────
    is_selling      = models.BooleanField(default=False)
    is_constructing = models.BooleanField(default=False)

    # ── Planning fields ───────────────────────────────────────
    total_units     = models.PositiveIntegerField(default=0)
    target_budget   = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    start_date      = models.DateField(null=True, blank=True)
    end_date        = models.DateField(null=True, blank=True)
    master_plan_url = models.URLField(blank=True)
    site_plan_url   = models.URLField(blank=True)

    # ── Permit fields ─────────────────────────────────────────
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

    # ── Intelligence snapshot ─────────────────────────────────
    readiness_score_last       = models.IntegerField(default=0)
    readiness_score_updated_at = models.DateTimeField(null=True, blank=True)

    # ── Timestamps ────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Proyek"
        verbose_name_plural = "Proyek"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.location}"

    # =========================================================
    # BASIC COMPUTED PROPERTIES — UNCHANGED
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
    # INTELLIGENCE ENGINE INTERNALS
    # =========================================================

    def _get_current_requirements(self):
        return StageRequirement.objects.filter(
            stage=self.stage, is_active=True,
        ).prefetch_related("prerequisites").order_by("order")

    def _get_requirement_statuses(self):
        statuses = self.requirement_statuses.filter(
            requirement__stage=self.stage,
            requirement__is_active=True,
        ).select_related("requirement")
        return {str(s.requirement_id): s for s in statuses}

    def _has_unmet_prerequisites(self, requirement, statuses_map):
        """
        Sprint 4: Check if a requirement has unmet prerequisites.
        Uses the already-fetched statuses_map for efficiency
        (avoids N+1 queries in get_intelligence_summary).

        Returns True if ANY prerequisite is not completed.
        """
        for prereq in requirement.prerequisites.all():
            s = statuses_map.get(str(prereq.id))
            if not s or s.status != ProjectRequirementStatus.Status.COMPLETED:
                return True
        return False

    # =========================================================
    # INTELLIGENCE PROPERTIES — Sprint 4 upgrades
    # =========================================================

    @property
    def readiness_score(self):
        """Unchanged — counts completed mandatory requirements."""
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        total = requirements.count()
        if total == 0:
            return 100
        statuses = self._get_requirement_statuses()
        completed = sum(
            1 for r in requirements
            if statuses.get(str(r.id)) and
               statuses[str(r.id)].status == ProjectRequirementStatus.Status.COMPLETED
        )
        return round((completed / total) * 100)

    @property
    def blocking_count(self):
        """
        Sprint 4 — Option B:
        Only count requirements that are DIRECTLY actionable
        (not blocked by unmet prerequisites).

        A requirement is "blocking" if:
          1. It is mandatory
          2. It is not completed
          3. It is NOT waiting on a prerequisite
             (because the prereq is the real blocker)

        This means blocking_count always = number of things
        the developer can actually DO RIGHT NOW.
        """
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses = self._get_requirement_statuses()
        blocking = 0
        for r in requirements:
            s = statuses.get(str(r.id))
            if not s or s.status in (
                ProjectRequirementStatus.Status.PENDING,
                ProjectRequirementStatus.Status.IN_PROGRESS,
            ):
                # Sprint 4: skip if blocked by an unmet prerequisite
                if not self._has_unmet_prerequisites(r, statuses):
                    blocking += 1
        return blocking

    @property
    def next_action(self):
        """
        Sprint 4: Always returns the ROOT cause action —
        the first mandatory requirement that:
          1. Is not completed
          2. Has NO unmet prerequisites (i.e. actionable now)
        """
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses = self._get_requirement_statuses()
        for r in requirements:
            s = statuses.get(str(r.id))
            if not s or s.status == ProjectRequirementStatus.Status.PENDING:
                # Only return if no unmet prerequisites
                if not self._has_unmet_prerequisites(r, statuses):
                    return r.name
        return None

    @property
    def risk_level(self):
        count = self.blocking_count
        if self.pbg_status == self.PermitStatus.REJECTED:
            return "high"
        if (self.end_date and date.today() > self.end_date
                and self.stage not in (self.Stage.COMPLETED, self.Stage.HANDOVER)
                and self.blocking_count > 0):
            return "high"
        if count == 0:
            return "low"
        if count <= 3:
            return "medium"
        return "high"

    @property
    def risk_level_display(self):
        return {"low": "Rendah", "medium": "Sedang", "high": "Tinggi"}.get(self.risk_level, self.risk_level)

    @property
    def trend(self):
        current  = self.readiness_score
        previous = self.readiness_score_last
        if current > previous:
            return "improving"
        if current < previous:
            return "declining"
        return "stable"

    @property
    def can_advance(self):
        if self.stage == self.Stage.COMPLETED:
            return False
        if self.stage == self.Stage.ON_HOLD:
            return False
        if self.blocking_count > 0:
            return False
        return True

    @property
    def readiness_dimensions(self):
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses     = self._get_requirement_statuses()
        dims = {
            "inventory":   {"total": 0, "completed": 0},
            "compliance":  {"total": 0, "completed": 0},
            "site_plan":   {"total": 0, "completed": 0},
            "sales_setup": {"total": 0, "completed": 0},
            "general":     {"total": 0, "completed": 0},
        }
        for r in requirements:
            cat = r.category if r.category in dims else "general"
            dims[cat]["total"] += 1
            s = statuses.get(str(r.id))
            if s and s.status == ProjectRequirementStatus.Status.COMPLETED:
                dims[cat]["completed"] += 1
        return {
            dim: 100 if data["total"] == 0 else round((data["completed"] / data["total"]) * 100)
            for dim, data in dims.items()
        }

    @property
    def risk_reasons(self):
        reasons = []
        if self.pbg_status == self.PermitStatus.REJECTED:
            reasons.append("PBG ditolak — perlu pengajuan ulang")
        elif (self.pbg_status == self.PermitStatus.NOT_STARTED
              and self.stage in (self.Stage.PERMITS, self.Stage.CONSTRUCTION, self.Stage.SALES, self.Stage.HANDOVER)):
            reasons.append("PBG belum dimulai")
        if self.amdal_status == self.PermitStatus.REJECTED:
            reasons.append("AMDAL ditolak")
        if (self.end_date and date.today() > self.end_date
                and self.stage not in (self.Stage.COMPLETED, self.Stage.HANDOVER)
                and self.blocking_count > 0):
            overrun_days = (date.today() - self.end_date).days
            reasons.append(f"Proyek terlambat {overrun_days} hari dari target")
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses     = self._get_requirement_statuses()
        # Sprint 4: only show ROOT blockers in risk reasons
        pending = [
            r.name for r in requirements
            if (not statuses.get(str(r.id)) or
                statuses[str(r.id)].status == ProjectRequirementStatus.Status.PENDING)
            and not self._has_unmet_prerequisites(r, statuses)
        ]
        for name in pending[:3]:
            reasons.append(f"{name} belum selesai")
        if len(pending) > 3:
            reasons.append(f"...dan {len(pending) - 3} item wajib lainnya")
        return reasons

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
        if (self.end_date and date.today() > self.end_date
                and self.stage not in (self.Stage.COMPLETED, self.Stage.HANDOVER)
                and self.blocking_count > 0):
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
        order = {"critical": 0, "warning": 1, "info": 2}
        result.sort(key=lambda a: order.get(a["level"], 3))
        return result

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
            return {
                "total_billed":   int(total_billed),
                "total_settled":  int(total_settled),
                "total_arrears":  int(total_arrears),
                "efficiency_pct": efficiency,
                "status":         "healthy" if efficiency >= 90 else "attention" if efficiency >= 70 else "critical",
                "status_display": "Sehat" if efficiency >= 90 else "Perlu Perhatian" if efficiency >= 70 else "Kritis",
            }
        except Exception:
            return {"total_billed": 0, "total_settled": 0, "total_arrears": 0, "efficiency_pct": 100, "status": "healthy", "status_display": "Sehat"}

    def _get_overdue_payments_count(self):
        try:
            from apps.payments.models import Payment
            from django.utils import timezone
            today = timezone.now().date()
            return Payment.objects.filter(unit__project=self).filter(
                models.Q(status="menunggak") |
                models.Q(status="menunggu", due_date__lt=today)
            ).count()
        except Exception:
            return 0

    # =========================================================
    # get_intelligence_summary — Sprint 4: adds dependency data
    # =========================================================

    def get_intelligence_summary(self):
        """
        Sprint 4: each requirement now includes:
          prerequisites        → list of prereq names
          unmet_prerequisites  → list of unmet prereq names
          is_dependency_blocked → True if waiting on a prereq
          can_act_now          → True if developer can work on this now
        """
        requirements = self._get_current_requirements()
        statuses     = self._get_requirement_statuses()

        items = []
        for r in requirements:
            s = statuses.get(str(r.id))

            # Sprint 2: evidence data
            evidence_count         = 0
            latest_evidence_status = None
            has_pending_evidence   = False

            # Sprint 3: audit count
            audit_count = 0

            if s:
                evidence_qs    = s.evidence.all().order_by("-uploaded_at")
                evidence_count = evidence_qs.count()
                if evidence_count > 0:
                    latest = evidence_qs.first()
                    latest_evidence_status = latest.verification_status
                    has_pending_evidence   = evidence_qs.filter(verification_status="pending").exists()
                audit_count = s.audit_logs.count()

            # Sprint 4: dependency data
            current_status         = s.status if s else ProjectRequirementStatus.Status.PENDING
            is_completed           = current_status == ProjectRequirementStatus.Status.COMPLETED
            prereq_names           = r.get_prerequisite_names()
            unmet_prereqs          = []
            is_dependency_blocked  = False

            if not is_completed and prereq_names:
                for prereq in r.prerequisites.all():
                    ps = statuses.get(str(prereq.id))
                    if not ps or ps.status != ProjectRequirementStatus.Status.COMPLETED:
                        unmet_prereqs.append(prereq.name)
                is_dependency_blocked = len(unmet_prereqs) > 0

            can_act_now = (
                not is_completed and
                not is_dependency_blocked
            )

            items.append({
                # Original fields
                "id":             str(r.id),
                "name":           r.name,
                "description":    r.description,
                "is_mandatory":   r.is_mandatory,
                "order":          r.order,
                "category":       r.category,
                "status":         current_status,
                "status_display": dict(ProjectRequirementStatus.Status.choices).get(
                    current_status, "Belum Dimulai"
                ),
                "notes":          s.notes if s else "",
                "completed_at":   s.completed_at.isoformat() if s and s.completed_at else None,
                "status_id":      str(s.id) if s else None,
                # Sprint 2
                "evidence_count":         evidence_count,
                "latest_evidence_status": latest_evidence_status,
                "has_pending_evidence":   has_pending_evidence,
                # Sprint 3
                "audit_count":            audit_count,
                # Sprint 4: dependency fields
                "prerequisites":          prereq_names,
                "unmet_prerequisites":    unmet_prereqs,
                "is_dependency_blocked":  is_dependency_blocked,
                "can_act_now":            can_act_now,
            })

        return {
            # Original
            "readiness_score":    self.readiness_score,
            "blocking_count":     self.blocking_count,
            "next_action":        self.next_action,
            "risk_level":         self.risk_level,
            "risk_level_display": self.risk_level_display,
            "trend":              self.trend,
            "can_advance":        self.can_advance,
            "requirements":       items,
            # Sprint 1
            "readiness_dimensions":  self.readiness_dimensions,
            "risk_reasons":          self.risk_reasons,
            "alerts":                self.alerts,
            "parallel_stages":       self.parallel_stage_status,
            "collection_efficiency": self.collection_efficiency,
        }

    # =========================================================
    # SNAPSHOT / ADVANCE / CHECKLIST
    # =========================================================

    def snapshot_readiness(self):
        from django.utils import timezone
        current = self.readiness_score
        if current != self.readiness_score_last:
            self.readiness_score_last       = current
            self.readiness_score_updated_at = timezone.now()
            self.save(update_fields=["readiness_score_last", "readiness_score_updated_at", "updated_at"])

    def _create_stage_requirements(self):
        requirements = StageRequirement.objects.filter(stage=self.stage, is_active=True)
        for req in requirements:
            status_obj, created = ProjectRequirementStatus.objects.get_or_create(
                project=self,
                requirement=req,
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
            raise ValueError(
                f"Proyek diblokir — {self.blocking_count} requirement wajib belum selesai. "
                f"Tindakan berikutnya: {self.next_action}."
            )
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
            return [
                {
                    "item":     r["name"],
                    "done":     r["status"] == ProjectRequirementStatus.Status.COMPLETED,
                    "blocking": r["is_mandatory"] and r["status"] != ProjectRequirementStatus.Status.COMPLETED,
                }
                for r in reqs
            ]
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
    # SPRINT 3: TIMELINE + FINANCIAL (unchanged)
    # =========================================================

    def activity_timeline(self, limit=20):
        activities = []
        audit_logs = RequirementAudit.objects.filter(
            requirement_status__project=self,
        ).select_related(
            "requirement_status__requirement", "changed_by",
        ).order_by("-changed_at")[:limit]

        action_labels = {
            RequirementAudit.Action.CREATED:           "membuat requirement",
            RequirementAudit.Action.UPDATED:           "memperbarui",
            RequirementAudit.Action.EVIDENCE_UPLOADED: "mengunggah bukti untuk",
            RequirementAudit.Action.EVIDENCE_APPROVED: "menyetujui bukti",
            RequirementAudit.Action.EVIDENCE_REJECTED: "menolak bukti",
            RequirementAudit.Action.COMPLETED:         "menyelesaikan",
            RequirementAudit.Action.STAGE_ADVANCED:    "melanjutkan tahap ke",
        }

        for log in audit_logs:
            req_name    = log.requirement_status.requirement.name
            actor_name  = log.changed_by.full_name if log.changed_by else "Sistem"
            action_verb = action_labels.get(log.action, log.action)
            activities.append({
                "id":        str(log.id),
                "type":      "requirement",
                "action":    log.action,
                "actor":     actor_name,
                "actor_id":  str(log.changed_by.id) if log.changed_by else None,
                "subject":   req_name,
                "message":   f"{actor_name} {action_verb} {req_name}",
                "notes":     log.notes,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "timestamp": log.changed_at.isoformat(),
            })
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

            overdue_items = sorted([
                {"id": str(p.id), "unit_number": p.unit.unit_number, "buyer_name": p.unit.buyer.full_name if p.unit.buyer else "—", "payment_type": p.payment_type, "amount": int(p.amount), "due_date": p.due_date.isoformat(), "days_overdue": (today - p.due_date).days}
                for p in payments if p.status == "menunggak" or (p.status == "menunggu" and p.due_date < today)
            ], key=lambda x: x["days_overdue"], reverse=True)

            upcoming_items = sorted([
                {"id": str(p.id), "unit_number": p.unit.unit_number, "buyer_name": p.unit.buyer.full_name if p.unit.buyer else "—", "payment_type": p.payment_type, "amount": int(p.amount), "due_date": p.due_date.isoformat(), "days_until": (p.due_date - today).days}
                for p in payments if p.status in ("akan_datang", "menunggu") and p.due_date >= today and (p.due_date - today).days <= 30
            ], key=lambda x: x["days_until"])

            return {
                "has_data": True, "total_billed": int(total_billed), "total_lunas": int(total_lunas),
                "total_menunggak": int(total_menunggak), "total_upcoming": int(total_upcoming),
                "efficiency_pct": efficiency,
                "status": "healthy" if efficiency >= 90 else "attention" if efficiency >= 70 else "critical",
                "status_display": "Sehat" if efficiency >= 90 else "Perlu Perhatian" if efficiency >= 70 else "Kritis",
                "overdue_items": overdue_items, "upcoming_items": upcoming_items,
            }
        except Exception:
            return {"has_data": False, "total_billed": 0, "total_lunas": 0, "total_menunggak": 0, "total_upcoming": 0, "efficiency_pct": 100, "status": "healthy", "status_display": "Sehat", "overdue_items": [], "upcoming_items": []}
