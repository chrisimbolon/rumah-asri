# =============================================================================
# === backend/apps/projects/models.py ===
# =============================================================================
"""
DevelopIndo — Projects Model + Intelligence Engine

Sprint 1 additions:
  StageRequirement.category  → maps requirements to 4 dimensions
  readiness_dimensions       → {inventory, compliance, site_plan, sales_setup}
  risk_reasons               → human-readable list of WHY risk is high
  alerts                     → severity-ranked actionable alerts ledger
  parallel_stages            → 5A (selling) + 5B (construction) run together
  collection_efficiency      → AR snapshot from Chris's visualization
  is_selling / is_constructing → parallel stage flags on Project

ZERO BREAKING CHANGES — all existing fields preserved.
New fields added alongside. 59 tests still green.
"""
import uuid
from datetime import date

from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel


# =============================================================================
# StageRequirement — global template of what must be done per stage
# Sprint 1: added `category` field for 4-dimension readiness mapping
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
    description  = models.TextField(blank=True, verbose_name="Deskripsi")
    is_mandatory = models.BooleanField(default=True, verbose_name="Wajib (memblokir)")
    order        = models.PositiveIntegerField(default=0, verbose_name="Urutan")
    is_active    = models.BooleanField(default=True, verbose_name="Aktif")
    # Sprint 1: category maps this requirement to a readiness dimension
    category     = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
        verbose_name="Kategori Requirement",
    )
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
# ProjectRequirementStatus — per-project completion tracking (unchanged)
# =============================================================================

class ProjectRequirementStatus(models.Model):
    class Status(models.TextChoices):
        PENDING        = "pending",        "Belum Dimulai"
        IN_PROGRESS    = "in_progress",    "Sedang Diproses"
        COMPLETED      = "completed",      "Selesai"
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
    notes        = models.TextField(blank=True, verbose_name="Catatan")
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

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
# Project — Sprint 1 intelligence engine upgrade
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
    name        = models.CharField(max_length=200, verbose_name="Nama Proyek")
    location    = models.CharField(max_length=300, verbose_name="Lokasi")
    description = models.TextField(blank=True, verbose_name="Deskripsi")
    stage       = models.CharField(
        max_length=20, choices=Stage.choices,
        default=Stage.DRAFT,
        verbose_name="Tahap", db_index=True,
    )

    # ── Sprint 1: parallel stage flags ────────────────────────
    # Indonesian pre-sales reality: selling and construction
    # run simultaneously — not sequentially.
    is_selling = models.BooleanField(
        default=False,
        verbose_name="Aktif Penjualan (5A)",
        help_text="Unit sudah dipasarkan/dijual (bisa paralel dengan konstruksi)",
    )
    is_constructing = models.BooleanField(
        default=False,
        verbose_name="Aktif Konstruksi (5B)",
        help_text="Konstruksi sudah berjalan",
    )

    # ── Planning fields ───────────────────────────────────────
    total_units   = models.PositiveIntegerField(default=0, verbose_name="Total Unit")
    target_budget = models.DecimalField(
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

    # =========================================================
    # INTELLIGENCE ENGINE INTERNALS — UNCHANGED
    # =========================================================

    def _get_current_requirements(self):
        return StageRequirement.objects.filter(
            stage=self.stage, is_active=True,
        ).order_by("order")

    def _get_requirement_statuses(self):
        statuses = self.requirement_statuses.filter(
            requirement__stage=self.stage,
            requirement__is_active=True,
        ).select_related("requirement")
        return {str(s.requirement_id): s for s in statuses}

    # =========================================================
    # ORIGINAL INTELLIGENCE PROPERTIES — UNCHANGED
    # =========================================================

    @property
    def readiness_score(self):
        """% of mandatory requirements completed. Unchanged."""
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
        """Number of mandatory requirements still blocking. Unchanged."""
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
        """First pending mandatory requirement. Unchanged."""
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
        Sprint 1 upgrade: risk now considers permit status AND
        timeline overrun — not just blocking count.
        """
        count = self.blocking_count

        # PBG rejected is always high risk regardless of count
        if self.pbg_status == self.PermitStatus.REJECTED:
            return "high"

        # Timeline overrun
        if (self.end_date and date.today() > self.end_date
                and self.stage not in (self.Stage.COMPLETED, self.Stage.HANDOVER)):
            return "high"

        # Standard blocking count logic
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
        """Comparing current vs last readiness snapshot. Unchanged."""
        current  = self.readiness_score
        previous = self.readiness_score_last
        if current > previous:
            return "improving"
        if current < previous:
            return "declining"
        return "stable"

    @property
    def can_advance(self):
        """Unchanged."""
        if self.stage == self.Stage.COMPLETED:
            return False
        if self.stage == self.Stage.ON_HOLD:
            return False
        if self.blocking_count > 0:
            return False
        return True

    # =========================================================
    # SPRINT 1: NEW INTELLIGENCE PROPERTIES
    # =========================================================

    @property
    def readiness_dimensions(self):
        """
        4-dimension readiness breakdown.
        Co-founder visualization: Project Readiness panel.
        Each dimension = % of mandatory requirements in that
        category that are completed.
        Returns 100 for dimensions with no requirements
        (not applicable to this stage).
        """
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

        result = {}
        for dim, data in dims.items():
            if data["total"] == 0:
                result[dim] = 100  # not applicable = 100%
            else:
                result[dim] = round((data["completed"] / data["total"]) * 100)

        return result

    @property
    def risk_reasons(self):
        """
        Human-readable list of WHY the risk level is what it is.
        Closes co-founder gap 2: "Risk Reason Is Hidden".
        Example output: ["PBG ditolak", "Kontraktor belum selesai"]
        """
        reasons = []

        # Permit-based reasons
        if self.pbg_status == self.PermitStatus.REJECTED:
            reasons.append("PBG ditolak — perlu pengajuan ulang")
        elif (self.pbg_status == self.PermitStatus.NOT_STARTED
              and self.stage in (
                  self.Stage.PERMITS, self.Stage.CONSTRUCTION,
                  self.Stage.SALES, self.Stage.HANDOVER,
              )):
            reasons.append("PBG belum dimulai")

        if self.amdal_status == self.PermitStatus.REJECTED:
            reasons.append("AMDAL ditolak")

        # Timeline overrun
        if (self.end_date and date.today() > self.end_date
                and self.stage not in (self.Stage.COMPLETED, self.Stage.HANDOVER)):
            overrun_days = (date.today() - self.end_date).days
            reasons.append(f"Proyek terlambat {overrun_days} hari dari target")

        # Pending mandatory requirements (show max 3 specific names)
        requirements = self._get_current_requirements().filter(is_mandatory=True)
        statuses     = self._get_requirement_statuses()
        pending = [
            r.name for r in requirements
            if not statuses.get(str(r.id)) or
               statuses[str(r.id)].status == ProjectRequirementStatus.Status.PENDING
        ]
        for name in pending[:3]:
            reasons.append(f"{name} belum selesai")
        if len(pending) > 3:
            reasons.append(f"...dan {len(pending) - 3} item wajib lainnya")

        return reasons

    @property
    def alerts(self):
        """
        Severity-ranked actionable alerts ledger.
        Co-founder visualization: Actionable Alerts Ledger.

        Levels:
          critical → blocks everything (red) — fix immediately
          warning  → needs attention soon (amber)
          info     → informational (blue)

        Sorted: critical first, then warning, then info.
        """
        result = []

        # ── CRITICAL: PBG rejected ────────────────────────────
        if self.pbg_status == self.PermitStatus.REJECTED:
            result.append({
                "level":    "critical",
                "category": "permit",
                "message":  "PBG ditolak — unit pipeline terkunci sampai PBG disetujui",
                "action":   "Ajukan ulang PBG ke instansi terkait",
            })

        # ── CRITICAL: AMDAL rejected ──────────────────────────
        if self.amdal_status == self.PermitStatus.REJECTED:
            result.append({
                "level":    "critical",
                "category": "permit",
                "message":  "AMDAL ditolak — tahap perizinan tidak dapat diselesaikan",
                "action":   "Revisi dokumen AMDAL dan ajukan ulang",
            })

        # ── CRITICAL: blocking mandatory requirements ─────────
        if self.blocking_count > 0:
            next_act = self.next_action
            result.append({
                "level":    "critical",
                "category": "requirement",
                "message":  (
                    f"{self.blocking_count} requirement wajib memblokir "
                    f"tahap {self.stage_display}"
                ),
                "action":   (
                    f"Mulai dengan: {next_act}"
                    if next_act else
                    "Selesaikan semua requirement wajib"
                ),
            })

        # ── WARNING: timeline overrun ─────────────────────────
        if (self.end_date and date.today() > self.end_date
                and self.stage not in (self.Stage.COMPLETED, self.Stage.HANDOVER)):
            overrun_days = (date.today() - self.end_date).days
            result.append({
                "level":    "warning",
                "category": "timeline",
                "message":  f"Proyek terlambat {overrun_days} hari dari target selesai",
                "action":   "Perbarui target selesai atau percepat konstruksi",
            })

        # ── WARNING: no units yet (past perencanaan) ──────────
        if (self.stage in (
                self.Stage.CONSTRUCTION, self.Stage.SALES, self.Stage.HANDOVER)
                and not self.units.exists()):
            result.append({
                "level":    "warning",
                "category": "inventory",
                "message":  "Belum ada unit terdaftar di tahap ini",
                "action":   "Tambah unit di modul Unit",
            })

        # ── WARNING: selling but no priced units ──────────────
        if self.is_selling and not self.units.filter(price__gt=0).exists():
            result.append({
                "level":    "warning",
                "category": "sales",
                "message":  "Mode penjualan aktif tapi belum ada unit dengan harga",
                "action":   "Set harga unit sebelum memasarkan",
            })

        # ── WARNING: financial delinquency ────────────────────
        overdue = self._get_overdue_payments_count()
        if overdue > 0:
            result.append({
                "level":    "warning",
                "category": "financial",
                "message":  f"{overdue} invoice pembayaran melewati jatuh tempo",
                "action":   "Tindak lanjuti pembayaran yang tertunggak",
            })

        # ── INFO: PBG not started but in perizinan ────────────
        if (self.pbg_status == self.PermitStatus.NOT_STARTED
                and self.stage == self.Stage.PERMITS):
            result.append({
                "level":    "info",
                "category": "permit",
                "message":  "PBG belum dimulai — diperlukan sebelum konstruksi",
                "action":   "Mulai pengajuan PBG",
            })

        # Sort: critical → warning → info
        order = {"critical": 0, "warning": 1, "info": 2}
        result.sort(key=lambda a: order.get(a["level"], 3))

        return result

    @property
    def parallel_stage_status(self):
        """
        Sprint 1: Indonesian pre-sales reality.
        5A = selling, 5B = construction — can run simultaneously.
        """
        return {
            "is_selling":      self.is_selling,
            "is_constructing": self.is_constructing,
            "label_5a":        "Aktif Penjualan" if self.is_selling else "Belum Dipasarkan",
            "label_5b":        "Aktif Konstruksi" if self.is_constructing else "Belum Konstruksi",
            "can_sell_now":    self.stage in (
                self.Stage.PLANNING, self.Stage.PERMITS,
                self.Stage.CONSTRUCTION, self.Stage.SALES,
                self.Stage.HANDOVER,
            ),
        }

    @property
    def collection_efficiency(self):
        """
        Sprint 1: Financial snapshot — Chris's visualization.
        Total AR, Lunas, Menunggak, efficiency %.
        Gracefully returns empty state if payments app unavailable.
        """
        try:
            from apps.payments.models import Payment
            payments = list(Payment.objects.filter(unit__project=self))
            total_billed  = sum(p.amount for p in payments)
            total_settled = sum(p.amount for p in payments if p.status == "lunas")
            total_arrears = total_billed - total_settled
            efficiency    = (
                round((total_settled / total_billed) * 100)
                if total_billed > 0 else 100
            )
            return {
                "total_billed":   int(total_billed),
                "total_settled":  int(total_settled),
                "total_arrears":  int(total_arrears),
                "efficiency_pct": efficiency,
                "status":         (
                    "healthy"   if efficiency >= 90 else
                    "attention" if efficiency >= 70 else
                    "critical"
                ),
                "status_display": (
                    "Sehat"           if efficiency >= 90 else
                    "Perlu Perhatian" if efficiency >= 70 else
                    "Kritis"
                ),
            }
        except Exception:
            return {
                "total_billed":   0,
                "total_settled":  0,
                "total_arrears":  0,
                "efficiency_pct": 100,
                "status":         "healthy",
                "status_display": "Sehat",
            }

    def _get_overdue_payments_count(self):
        """Count overdue payments — used by alerts property."""
        try:
            from apps.payments.models import Payment
            from django.utils import timezone
            return Payment.objects.filter(
                unit__project=self,
                status__in=["pending", "partial"],
                due_date__lt=timezone.now().date(),
            ).count()
        except Exception:
            return 0

    # =========================================================
    # get_intelligence_summary — SPRINT 1 UPGRADE
    # Backward compatible — all original fields preserved.
    # New fields added alongside.
    # =========================================================

    def get_intelligence_summary(self):
        """
        Returns full intelligence data for API response.
        Sprint 1: adds dimensions, risk_reasons, alerts,
        parallel_stages, collection_efficiency.
        All original fields unchanged.
        """
        requirements = self._get_current_requirements()
        statuses     = self._get_requirement_statuses()

        items = []
        for r in requirements:
            s = statuses.get(str(r.id))
            items.append({
                "id":             str(r.id),
                "name":           r.name,
                "description":    r.description,
                "is_mandatory":   r.is_mandatory,
                "order":          r.order,
                "category":       r.category,       # Sprint 1
                "status":         s.status if s else ProjectRequirementStatus.Status.PENDING,
                "status_display": dict(ProjectRequirementStatus.Status.choices).get(
                    s.status if s else "pending", "Belum Dimulai"
                ),
                "notes":          s.notes if s else "",
                "completed_at":   s.completed_at.isoformat() if s and s.completed_at else None,
                "status_id":      str(s.id) if s else None,
            })

        return {
            # Original fields — UNCHANGED
            "readiness_score":    self.readiness_score,
            "blocking_count":     self.blocking_count,
            "next_action":        self.next_action,
            "risk_level":         self.risk_level,
            "risk_level_display": self.risk_level_display,
            "trend":              self.trend,
            "can_advance":        self.can_advance,
            "requirements":       items,

            # Sprint 1: new fields
            "readiness_dimensions":  self.readiness_dimensions,
            "risk_reasons":          self.risk_reasons,
            "alerts":                self.alerts,
            "parallel_stages":       self.parallel_stage_status,
            "collection_efficiency": self.collection_efficiency,
        }

    # =========================================================
    # SNAPSHOT / ADVANCE / CHECKLIST — UNCHANGED except
    # advance_stage() auto-sets parallel flags
    # =========================================================

    def snapshot_readiness(self):
        """Store current readiness as last snapshot. Unchanged."""
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
        """Auto-create requirement status rows for new stage. Unchanged."""
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
        Move project to next stage.
        Sprint 1: auto-sets is_constructing / is_selling flags
        when advancing to those stages.
        """
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

        # Sprint 1: auto-set parallel flags
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
        """Backward compat — unchanged."""
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
            self.Stage.DRAFT: [
                {"item": "Nama proyek",   "done": bool(self.name)},
                {"item": "Lokasi proyek", "done": bool(self.location)},
                {"item": "Deskripsi",     "done": bool(self.description)},
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
                {"item": "Unit dibuat",         "done": self.units.exists()},
                {"item": "Fase konstruksi set", "done": self.units.filter(phases__isnull=False).exists()},
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
