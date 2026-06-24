# =============================================================================
# === backend/apps/projects/models.py ===
# =============================================================================
"""
DevelopIndo — Projects Model + Intelligence Engine

Lifecycle stages (in order):
  draft → perencanaan → perizinan → konstruksi → penjualan → serah_terima → selesai

Intelligence layer (from co-founder's visualization):
  StageRequirement      — what must be completed per stage (global template)
  ProjectRequirementStatus — per-project completion tracking
  readiness_score       — % of mandatory requirements completed
  blocking_count        — number of mandatory items still pending
  next_action           — first pending mandatory requirement
  risk_level            — High/Medium/Low based on blocking count
  trend                 — Improving/Stable/Declining vs last snapshot
"""
import uuid
from datetime import date

from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel


# =============================================================================
# StageRequirement — global template of what must be done per stage
# =============================================================================

class StageRequirement(models.Model):
    """
    Defines what requirements exist for each lifecycle stage.
    These are GLOBAL — shared across all projects.
    Future: per-template requirements (Perumahan vs Apartemen vs Komersial).
    
    is_mandatory = True  → blocks stage advancement if not completed
    is_mandatory = False → shown as checklist but doesn't block
    """

    class Stage(models.TextChoices):
        DRAFT        = "draft",        "Draft"
        PLANNING     = "perencanaan",  "Perencanaan"
        PERMITS      = "perizinan",    "Perizinan"
        CONSTRUCTION = "konstruksi",   "Konstruksi"
        SALES        = "penjualan",    "Penjualan"
        HANDOVER     = "serah_terima", "Serah Terima"
        COMPLETED    = "selesai",      "Selesai"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stage        = models.CharField(max_length=20, choices=Stage.choices, db_index=True)
    name         = models.CharField(max_length=200, verbose_name="Nama Requirement")
    description  = models.TextField(blank=True,    verbose_name="Deskripsi")
    is_mandatory = models.BooleanField(default=True, verbose_name="Wajib (memblokir)")
    order        = models.PositiveIntegerField(default=0, verbose_name="Urutan")
    is_active    = models.BooleanField(default=True, verbose_name="Aktif")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Stage Requirement"
        verbose_name_plural = "Stage Requirements"
        ordering            = ["stage", "order"]
        unique_together     = [["stage", "name"]]

    def __str__(self):
        flag = "⚡" if self.is_mandatory else "○"
        return f"{flag} [{self.get_stage_display()}] {self.name}"


# =============================================================================
# ProjectRequirementStatus — per-project completion tracking
# =============================================================================

class ProjectRequirementStatus(models.Model):
    """
    Tracks the completion status of each StageRequirement for each Project.
    Auto-created when a project advances to a new stage.
    Updated by developers as they complete each item.
    """

    class Status(models.TextChoices):
        PENDING     = "pending",        "Belum Dimulai"
        IN_PROGRESS = "in_progress",    "Sedang Diproses"
        COMPLETED   = "completed",      "Selesai"
        NOT_APPLICABLE = "not_applicable", "Tidak Berlaku"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project     = models.ForeignKey(
        "Project", on_delete=models.CASCADE,
        related_name="requirement_statuses",
    )
    requirement = models.ForeignKey(
        StageRequirement, on_delete=models.CASCADE,
        related_name="project_statuses",
    )
    status      = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.PENDING,
    )
    notes       = models.TextField(blank=True, verbose_name="Catatan")
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Project Requirement Status"
        verbose_name_plural = "Project Requirement Statuses"
        unique_together     = [["project", "requirement"]]
        ordering            = ["requirement__order"]

    def __str__(self):
        return f"{self.project.name} — {self.requirement.name}: {self.status}"

    def mark_completed(self, user=None):
        from django.utils import timezone
        self.status       = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.updated_by   = user
        self.save(update_fields=["status", "completed_at", "updated_by", "updated_at"])


# =============================================================================
# Project — main model with intelligence engine
# =============================================================================

class Project(TenantScopedModel):

    # ── Lifecycle stages ──────────────────────────────────────
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
    name        = models.CharField(max_length=200, verbose_name="Nama Proyek")
    location    = models.CharField(max_length=300, verbose_name="Lokasi")
    description = models.TextField(blank=True, verbose_name="Deskripsi")
    stage       = models.CharField(
        max_length=20, choices=Stage.choices,
        default=Stage.DRAFT,
        verbose_name="Tahap", db_index=True,
    )

    # ── Planning fields ───────────────────────────────────────
    total_units     = models.PositiveIntegerField(default=0, verbose_name="Total Unit")
    target_budget   = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True, verbose_name="Target Anggaran (Rp)",
    )
    start_date      = models.DateField(null=True, blank=True, verbose_name="Tanggal Mulai")
    end_date        = models.DateField(null=True, blank=True, verbose_name="Target Selesai")
    master_plan_url = models.URLField(blank=True, verbose_name="URL Master Plan")
    site_plan_url   = models.URLField(blank=True, verbose_name="URL Site Plan")

    # ── Permit fields ─────────────────────────────────────────
    class PermitStatus(models.TextChoices):
        NOT_STARTED = "belum",    "Belum Dimulai"
        IN_PROGRESS = "proses",   "Sedang Diproses"
        APPROVED    = "approved", "Disetujui"
        REJECTED    = "rejected", "Ditolak"

    ipr_status   = models.CharField(max_length=20, choices=PermitStatus.choices, default=PermitStatus.NOT_STARTED, verbose_name="Status IPR")
    ipr_date     = models.DateField(null=True, blank=True, verbose_name="Tanggal IPR")
    amdal_status = models.CharField(max_length=20, choices=PermitStatus.choices, default=PermitStatus.NOT_STARTED, verbose_name="Status AMDAL/UKL-UPL")
    amdal_date   = models.DateField(null=True, blank=True, verbose_name="Tanggal AMDAL")
    pbg_status   = models.CharField(max_length=20, choices=PermitStatus.choices, default=PermitStatus.NOT_STARTED, verbose_name="Status PBG")
    pbg_date     = models.DateField(null=True, blank=True, verbose_name="Tanggal PBG Diterbitkan")

    # ── Intelligence snapshot fields ──────────────────────────
    # Stores previous readiness score for trend calculation.
    # Updated whenever readiness_score changes significantly.
    readiness_score_last       = models.IntegerField(default=0, verbose_name="Readiness Score Sebelumnya")
    readiness_score_updated_at = models.DateTimeField(null=True, blank=True, verbose_name="Readiness Score Diperbarui")

    # ── Timestamps ────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Proyek"
        verbose_name_plural = "Proyek"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.location}"

    # ── Basic computed properties ─────────────────────────────

    @property
    def units_sold(self):
        return self.units.filter(
            status__in=["terjual", "proses", "serah_terima"]
        ).count()

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

    # ── Intelligence Engine ───────────────────────────────────

    def _get_current_requirements(self):
        """All active requirements for the current stage."""
        return StageRequirement.objects.filter(
            stage=self.stage,
            is_active=True,
        ).order_by("order")

    def _get_requirement_statuses(self):
        """
        ProjectRequirementStatus rows for this project's current stage.
        Returns dict: {requirement_id: status_obj}
        """
        statuses = self.requirement_statuses.filter(
            requirement__stage=self.stage,
            requirement__is_active=True,
        ).select_related("requirement")
        return {str(s.requirement_id): s for s in statuses}

    @property
    def readiness_score(self):
        """
        % of mandatory requirements completed for current stage.
        Formula: completed_mandatory / total_mandatory × 100
        Returns 100 if no mandatory requirements exist (stage is open).
        """
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        total = requirements.count()
        if total == 0:
            return 100

        statuses = self._get_requirement_statuses()
        completed = sum(
            1 for r in requirements
            if statuses.get(str(r.id), None) and
               statuses[str(r.id)].status == ProjectRequirementStatus.Status.COMPLETED
        )
        return round((completed / total) * 100)

    @property
    def blocking_count(self):
        """
        Number of mandatory requirements still pending or in_progress.
        This is what blocks stage advancement.
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
                blocking += 1
        return blocking

    @property
    def next_action(self):
        """
        First pending mandatory requirement (ordered by requirement order).
        This is the single most important thing for the developer to do next.
        Returns None if all mandatory requirements are complete.
        """
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses = self._get_requirement_statuses()
        for r in requirements:
            s = statuses.get(str(r.id))
            if not s or s.status == ProjectRequirementStatus.Status.PENDING:
                return r.name
        return None

    @property
    def risk_level(self):
        """
        Simple v1 risk assessment based on blocking count.
        High:   > 3 mandatory pending
        Medium: 1-3 mandatory pending
        Low:    0 mandatory pending (all done)
        """
        count = self.blocking_count
        if count == 0:
            return "low"
        if count <= 3:
            return "medium"
        return "high"

    @property
    def risk_level_display(self):
        return {"low": "Rendah", "medium": "Sedang", "high": "Tinggi"}.get(
            self.risk_level, self.risk_level
        )

    @property
    def trend(self):
        """
        Compares current readiness_score to readiness_score_last.
        improving → score went up
        declining → score went down
        stable    → no change
        """
        current  = self.readiness_score
        previous = self.readiness_score_last
        if current > previous:
            return "improving"
        if current < previous:
            return "declining"
        return "stable"

    @property
    def can_advance(self):
        """
        Project can advance if blocking_count is 0.
        Also checks the legacy PBG rule as a safety net.
        """
        if self.stage == self.Stage.COMPLETED:
            return False
        if self.stage == self.Stage.ON_HOLD:
            return False
        # Intelligence engine: block if any mandatory requirement pending
        if self.blocking_count > 0:
            return False
        return True

    def get_intelligence_summary(self):
        """
        Returns full intelligence data for API response and dashboard.
        Includes all requirements with their current status.
        """
        requirements = self._get_current_requirements()
        statuses     = self._get_requirement_statuses()

        items = []
        for r in requirements:
            s = statuses.get(str(r.id))
            items.append({
                "id":           str(r.id),
                "name":         r.name,
                "description":  r.description,
                "is_mandatory": r.is_mandatory,
                "order":        r.order,
                "status":       s.status if s else ProjectRequirementStatus.Status.PENDING,
                "status_display": dict(ProjectRequirementStatus.Status.choices).get(
                    s.status if s else "pending", "Belum Dimulai"
                ),
                "notes":        s.notes if s else "",
                "completed_at": s.completed_at.isoformat() if s and s.completed_at else None,
                "status_id":    str(s.id) if s else None,
            })

        return {
            "readiness_score": self.readiness_score,
            "blocking_count":  self.blocking_count,
            "next_action":     self.next_action,
            "risk_level":      self.risk_level,
            "risk_level_display": self.risk_level_display,
            "trend":           self.trend,
            "can_advance":     self.can_advance,
            "requirements":    items,
        }

    def snapshot_readiness(self):
        """
        Store current readiness_score as the 'last' snapshot.
        Call this when requirements change to enable trend tracking.
        """
        from django.utils import timezone
        current = self.readiness_score
        if current != self.readiness_score_last:
            self.readiness_score_last       = current
            self.readiness_score_updated_at = timezone.now()
            self.save(update_fields=[
                "readiness_score_last",
                "readiness_score_updated_at",
                "updated_at",
            ])

    def _create_stage_requirements(self):
        """
        Auto-create ProjectRequirementStatus rows when advancing to a new stage.
        Called by advance_stage() so every new stage starts with all
        requirements in PENDING status.
        """
        requirements = StageRequirement.objects.filter(
            stage=self.stage, is_active=True
        )
        for req in requirements:
            ProjectRequirementStatus.objects.get_or_create(
                project=self,
                requirement=req,
                defaults={"status": ProjectRequirementStatus.Status.PENDING},
            )

    def advance_stage(self):
        """
        Move project to next lifecycle stage.
        Raises ValueError if any mandatory requirement is blocking.
        Auto-creates requirement status rows for the new stage.
        """
        if self.stage == self.Stage.COMPLETED:
            raise ValueError("Proyek sudah selesai.")
        if self.stage == self.Stage.ON_HOLD:
            raise ValueError("Proyek sedang ditunda.")

        # Intelligence engine blocking check
        if self.blocking_count > 0:
            next_action = self.next_action
            raise ValueError(
                f"Proyek diblokir — {self.blocking_count} requirement wajib belum selesai. "
                f"Tindakan berikutnya: {next_action}."
            )

        # Snapshot current score before advancing
        self.snapshot_readiness()

        # Advance
        self.stage = self.next_stage
        self.save(update_fields=["stage", "updated_at"])

        # Auto-create requirement statuses for new stage
        self._create_stage_requirements()

        return self.stage

    # ── Legacy checklist (kept for backward compat) ───────────
    @property
    def stage_checklist(self):
        """
        Returns intelligence summary requirements formatted as checklist.
        Replaces the old hardcoded dict — now driven by StageRequirement table.
        Falls back to hardcoded if no StageRequirement rows exist for this stage.
        """
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

        # Hardcoded fallback (used before seed_stage_requirements runs)
        hardcoded = {
            self.Stage.DRAFT: [
                {"item": "Nama proyek",    "done": bool(self.name)},
                {"item": "Lokasi proyek",  "done": bool(self.location)},
                {"item": "Deskripsi",      "done": bool(self.description)},
            ],
            self.Stage.PLANNING: [
                {"item": "Total unit",      "done": self.total_units > 0},
                {"item": "Tanggal mulai",   "done": bool(self.start_date)},
                {"item": "Target selesai",  "done": bool(self.end_date)},
                {"item": "Target anggaran", "done": bool(self.target_budget)},
            ],
            self.Stage.PERMITS: [
                {"item": "IPR disetujui",   "done": self.ipr_status   == self.PermitStatus.APPROVED},
                {"item": "AMDAL disetujui", "done": self.amdal_status == self.PermitStatus.APPROVED},
                {"item": "PBG diterbitkan", "done": self.pbg_status   == self.PermitStatus.APPROVED, "blocking": True},
            ],
            self.Stage.CONSTRUCTION: [
                {"item": "Unit dibuat",        "done": self.units.exists()},
                {"item": "Fase konstruksi set","done": self.units.filter(phases__isnull=False).exists()},
            ],
            self.Stage.SALES: [
                {"item": "Harga unit ditetapkan", "done": self.units.filter(price__gt=0).exists()},
            ],
            self.Stage.HANDOVER: [
                {"item": "Semua unit selesai",
                 "done": not self.units.exclude(status="serah_terima").exists()},
            ],
        }
        return hardcoded.get(self.stage, [])
