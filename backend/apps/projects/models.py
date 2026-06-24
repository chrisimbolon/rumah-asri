# =============================================================================
# === backend/apps/projects/models.py ===
# =============================================================================
"""
DevelopIndo — Projects Model

Lifecycle stages (in order):
  draft → perencanaan → perizinan → konstruksi → penjualan → serah_terima → selesai

Key rules enforced at model level:
  - Units cannot move to "proses" unless project is at konstruksi or later
  - Project cannot advance to konstruksi without PBG permit approved
"""
import uuid

from django.db import models

from apps.core.models import TenantScopedModel


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

    # Stage order for advancement validation
    STAGE_ORDER = [
        Stage.DRAFT,
        Stage.PLANNING,
        Stage.PERMITS,
        Stage.CONSTRUCTION,
        Stage.SALES,
        Stage.HANDOVER,
        Stage.COMPLETED,
    ]

    # ── Core fields ───────────────────────────────────────────
    name        = models.CharField(max_length=200, verbose_name="Nama Proyek")
    location    = models.CharField(max_length=300, verbose_name="Lokasi")
    description = models.TextField(blank=True, verbose_name="Deskripsi")

    # Lifecycle stage — replaces the old binary status field
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.DRAFT,
        verbose_name="Tahap",
        db_index=True,
    )

    # ── Planning stage fields ─────────────────────────────────
    total_units    = models.PositiveIntegerField(default=0,  verbose_name="Total Unit")
    target_budget  = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name="Target Anggaran (Rp)",
    )
    start_date     = models.DateField(null=True, blank=True, verbose_name="Tanggal Mulai")
    end_date       = models.DateField(null=True, blank=True, verbose_name="Target Selesai")
    master_plan_url = models.URLField(blank=True, verbose_name="URL Master Plan")
    site_plan_url   = models.URLField(blank=True, verbose_name="URL Site Plan")

    # ── Permit stage fields ───────────────────────────────────
    class PermitStatus(models.TextChoices):
        NOT_STARTED = "belum",    "Belum Dimulai"
        IN_PROGRESS = "proses",   "Sedang Diproses"
        APPROVED    = "approved", "Disetujui"
        REJECTED    = "rejected", "Ditolak"

    ipr_status  = models.CharField(
        max_length=20, choices=PermitStatus.choices,
        default=PermitStatus.NOT_STARTED,
        verbose_name="Status IPR",
    )
    ipr_date    = models.DateField(null=True, blank=True, verbose_name="Tanggal IPR")

    amdal_status = models.CharField(
        max_length=20, choices=PermitStatus.choices,
        default=PermitStatus.NOT_STARTED,
        verbose_name="Status AMDAL/UKL-UPL",
    )
    amdal_date  = models.DateField(null=True, blank=True, verbose_name="Tanggal AMDAL")

    pbg_status  = models.CharField(
        max_length=20, choices=PermitStatus.choices,
        default=PermitStatus.NOT_STARTED,
        verbose_name="Status PBG",
    )
    pbg_date    = models.DateField(null=True, blank=True, verbose_name="Tanggal PBG Diterbitkan")

    # ── Timestamps ───────────────────────────────────────────
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Proyek"
        verbose_name_plural = "Proyek"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.location}"

    # ── Computed properties ───────────────────────────────────

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
    def can_advance(self):
        """Whether this project can move to the next stage."""
        if self.stage == self.Stage.COMPLETED:
            return False
        if self.stage == self.Stage.ON_HOLD:
            return False
        # Cannot advance to konstruksi without PBG approved
        if self.stage == self.Stage.PERMITS:
            return self.pbg_status == self.PermitStatus.APPROVED
        return True

    @property
    def next_stage(self):
        """The next stage in the lifecycle, or None if at end."""
        if self.stage not in self.STAGE_ORDER:
            return None
        idx = self.STAGE_ORDER.index(self.stage)
        if idx + 1 >= len(self.STAGE_ORDER):
            return None
        return self.STAGE_ORDER[idx + 1]

    @property
    def stage_checklist(self):
        """
        Returns a checklist of what's needed for the current stage
        and what's blocking advancement to the next stage.
        """
        checklist = {
            self.Stage.DRAFT: [
                {"item": "Nama proyek",    "done": bool(self.name)},
                {"item": "Lokasi proyek",  "done": bool(self.location)},
                {"item": "Deskripsi",      "done": bool(self.description)},
            ],
            self.Stage.PLANNING: [
                {"item": "Total unit",     "done": self.total_units > 0},
                {"item": "Tanggal mulai",  "done": bool(self.start_date)},
                {"item": "Target selesai", "done": bool(self.end_date)},
                {"item": "Target anggaran","done": bool(self.target_budget)},
            ],
            self.Stage.PERMITS: [
                {"item": "IPR disetujui",   "done": self.ipr_status   == self.PermitStatus.APPROVED},
                {"item": "AMDAL disetujui", "done": self.amdal_status == self.PermitStatus.APPROVED},
                {"item": "PBG diterbitkan", "done": self.pbg_status   == self.PermitStatus.APPROVED,
                 "blocking": True},
            ],
            self.Stage.CONSTRUCTION: [
                {"item": "Unit dibuat",       "done": self.units.exists()},
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
        return checklist.get(self.stage, [])

    def advance_stage(self):
        """
        Move project to next lifecycle stage.
        Raises ValueError if advancement is blocked.
        """
        if not self.can_advance:
            if self.stage == self.Stage.PERMITS:
                raise ValueError(
                    "PBG (Persetujuan Bangunan Gedung) harus disetujui "
                    "sebelum proyek dapat memasuki tahap konstruksi."
                )
            raise ValueError(
                f"Proyek tidak dapat dilanjutkan dari tahap {self.stage_display}."
            )
        self.stage = self.next_stage
        self.save(update_fields=["stage", "updated_at"])
        return self.stage
