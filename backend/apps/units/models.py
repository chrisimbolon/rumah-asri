# =============================================================================
# === backend/apps/units/models.py ===
# =============================================================================
"""
DevelopIndo — Units Model

Status lifecycle:
  tersedia → dipesan → proses → terjual → serah_terima

"dipesan" (booked) is the critical pre-sales state:
  - Unit is reserved for a buyer
  - Booking fee has been paid
  - Construction may not have started yet
  - This is how Indonesian property market works —
    sell first, build second
"""
from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel
from apps.projects.models import Project


class Unit(TenantScopedModel):

    class Status(models.TextChoices):
        AVAILABLE   = "tersedia",     "Tersedia"
        BOOKED      = "dipesan",      "Dipesan"      # ← NEW: pre-sales state
        IN_PROGRESS = "proses",       "Proses"
        SOLD        = "terjual",      "Terjual"
        HANDOVER    = "serah_terima", "Serah Terima"

    # Sprint 22: legal forward/backward transitions. Single source of
    # truth — used by the serializer's validate() so both manual PUT
    # edits and any future booking-flow action (convert, handover) all
    # go through the same guard, same as the ProjectRequirementStatus
    # pattern this whole platform already trusts.
    VALID_TRANSITIONS = {
        Status.AVAILABLE:   {Status.BOOKED},
        Status.BOOKED:      {Status.AVAILABLE, Status.IN_PROGRESS},   # cancel or convert-to-sale
        Status.IN_PROGRESS: {Status.SOLD},
        Status.SOLD:        {Status.HANDOVER},
        Status.HANDOVER:    set(),   # terminal — nothing comes after handover
    }

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name="units", verbose_name="Proyek",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="units",
        limit_choices_to={"role": "buyer"},
        verbose_name="Pembeli",
    )

    unit_number       = models.CharField(max_length=20,  verbose_name="Nomor Unit")
    unit_type         = models.CharField(max_length=50,  verbose_name="Tipe Unit")
    land_area         = models.DecimalField(max_digits=8,  decimal_places=2, verbose_name="Luas Tanah (m²)")
    building_area     = models.DecimalField(max_digits=8,  decimal_places=2, verbose_name="Luas Bangunan (m²)")
    price             = models.BigIntegerField(verbose_name="Harga (IDR)")
    status            = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.AVAILABLE, verbose_name="Status",
    )
    progress          = models.PositiveIntegerField(default=0,   verbose_name="Progres (%)")
    current_phase     = models.CharField(max_length=200, blank=True, verbose_name="Fase Saat Ini")
    target_completion = models.DateField(null=True, blank=True,  verbose_name="Target Selesai")
    payment_method    = models.CharField(max_length=100, blank=True, verbose_name="Metode Pembayaran")
    bank              = models.CharField(max_length=50,  blank=True, verbose_name="Bank")
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Unit"
        verbose_name_plural = "Unit"
        ordering            = ["project", "unit_number"]
        unique_together     = ["project", "unit_number"]

    def __str__(self):
        return f"{self.project.name} — Unit {self.unit_number} ({self.unit_type})"

    def _resolve_organization(self):
        return self.project.organization

    def can_transition_to(self, new_status):
        """
        Sprint 22: is moving from the CURRENT status to new_status
        legal? Same-status "changes" (no-op edits) are always allowed.
        Returns (bool, reason_string) — mirrors the exact shape of
        ProjectRequirementStatus.can_complete() elsewhere in this
        codebase, so error handling stays consistent everywhere.
        """
        if new_status == self.status:
            return True, ""
        allowed = self.VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            return False, (
                f"Tidak dapat mengubah status dari "
                f"'{self.get_status_display()}' langsung ke "
                f"'{dict(self.Status.choices).get(new_status, new_status)}'."
            )
        return True, ""


# =============================================================================
# Booking — records the pre-sales transaction
# =============================================================================

class Booking(models.Model):
    """
    Records a unit booking (pre-sale).

    When a buyer books a unit:
      1. Booking record created
      2. Unit status → "dipesan"
      3. Unit.buyer set to the booking buyer
      4. SPR number auto-generated
      5. Booking fee recorded

    When booking is cancelled:
      1. Booking status → "cancelled"
      2. Unit status → "tersedia"
      3. Unit.buyer cleared

    When booking converts to full sale:
      1. Booking status → "converted"
      2. Unit status → "proses" or "terjual"
      3. Payment records created for full amount
    """

    class BookingStatus(models.TextChoices):
        ACTIVE    = "active",    "Aktif"
        CANCELLED = "cancelled", "Dibatalkan"
        CONVERTED = "converted", "Dikonversi ke Penjualan"

    id          = models.UUIDField(
        primary_key=True,
        default=__import__("uuid").uuid4,
        editable=False,
    )
    unit        = models.OneToOneField(
        Unit, on_delete=models.CASCADE,
        related_name="booking",
        verbose_name="Unit",
    )
    buyer       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
        limit_choices_to={"role": "buyer"},
        verbose_name="Pembeli",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Organisasi",
    )

    # ── Booking details ───────────────────────────────────────
    spr_number    = models.CharField(
        max_length=50, unique=True,
        verbose_name="Nomor SPR",
        help_text="Surat Pemesanan Rumah — auto-generated",
    )
    booking_fee   = models.BigIntegerField(
        verbose_name="Booking Fee (IDR)",
        help_text="Uang tanda jadi / booking fee",
    )
    booking_date  = models.DateField(verbose_name="Tanggal Booking")
    notes         = models.TextField(blank=True, verbose_name="Catatan")

    # ── Payment method ────────────────────────────────────────
    payment_method = models.CharField(
        max_length=100, blank=True,
        verbose_name="Metode Pembayaran",
        help_text="KPR BCA / Cash / KPR Mandiri etc.",
    )
    bank           = models.CharField(max_length=50, blank=True, verbose_name="Bank")

    # ── Status ────────────────────────────────────────────────
    status      = models.CharField(
        max_length=20, choices=BookingStatus.choices,
        default=BookingStatus.ACTIVE,
        verbose_name="Status Booking",
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="cancelled_bookings",
    )
    cancel_reason = models.TextField(blank=True, verbose_name="Alasan Pembatalan")

    # ── Audit ─────────────────────────────────────────────────
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name="created_bookings",
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Booking"
        verbose_name_plural = "Bookings"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.spr_number} — {self.unit} — {self.buyer}"

    @classmethod
    def generate_spr_number(cls, organization):
        """
        Auto-generate SPR number: SPR-{ORG_INITIALS}-{YEAR}-{SEQUENCE}
        Example: SPR-PASP-2026-001
        """
        from datetime import date
        year     = date.today().year
        initials = "".join(w[0].upper() for w in organization.name.split()[:4])
        count    = cls.objects.filter(
            organization=organization,
            created_at__year=year,
        ).count() + 1
        return f"SPR-{initials}-{year}-{count:03d}"


# =============================================================================
# UnitPriceHistory — Sprint 22: append-only log of price changes
# =============================================================================

class UnitPriceHistory(models.Model):
    """
    Sprint 22: written automatically whenever Unit.price changes via
    the update endpoint (see UnitCreateSerializer.update()) — never
    created or edited directly by hand. Append-only, ordered newest
    first, same "before/after snapshot" spirit as RequirementAudit.
    """
    id         = models.UUIDField(
        primary_key=True,
        default=__import__("uuid").uuid4,
        editable=False,
    )
    unit       = models.ForeignKey(
        Unit, on_delete=models.CASCADE,
        related_name="price_history",
        verbose_name="Unit",
    )
    old_price  = models.BigIntegerField(verbose_name="Harga Lama (IDR)")
    new_price  = models.BigIntegerField(verbose_name="Harga Baru (IDR)")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="unit_price_changes",
        verbose_name="Diubah Oleh",
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Riwayat Harga Unit"
        verbose_name_plural = "Riwayat Harga Unit"
        ordering            = ["-changed_at"]

    def __str__(self):
        return f"{self.unit.unit_number}: {self.old_price} → {self.new_price}"
