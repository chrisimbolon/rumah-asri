# =============================================================================
# === apps/payments/models.py ===
# =============================================================================
"""
DevelopIndo — Payments Model
"""
import uuid

from django.conf import settings
from django.db import models, transaction

from apps.core.models import TenantScopedModel
from apps.units.models import Unit


class Payment(TenantScopedModel):

    class Status(models.TextChoices):
        PAID         = "lunas",       "Lunas"
        PENDING      = "menunggu",    "Menunggu"
        OVERDUE      = "menunggak",   "Menunggak"
        UPCOMING     = "akan_datang", "Akan Datang"
        BANK_PROCESS = "proses_bank", "Proses Bank"

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="payments", verbose_name="Unit")

    payment_type = models.CharField(max_length=100, verbose_name="Jenis Pembayaran")
    due_date     = models.DateField(verbose_name="Jatuh Tempo")
    amount       = models.BigIntegerField(verbose_name="Jumlah (IDR)")
    status       = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UPCOMING, verbose_name="Status",
    )
    bank       = models.CharField(max_length=50, blank=True, verbose_name="Bank")
    paid_at    = models.DateTimeField(null=True, blank=True, verbose_name="Tanggal Bayar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Pembayaran"
        verbose_name_plural = "Pembayaran"
        ordering            = ["due_date"]

    def __str__(self):
        return f"Unit {self.unit.unit_number} — {self.payment_type} ({self.get_status_display()})"

    def _resolve_organization(self):
        return self.unit.organization

    @property
    def is_overdue(self):
        """
        Sprint 25: single source of truth for "is this payment actually
        overdue." Previously this exact definition was duplicated
        inconsistently — Project._get_overdue_payments_count() had it
        right (menunggak, OR menunggu past its due date), but
        Project.collection_efficiency computed arrears as a plain
        total_billed - total_settled, which silently counted payments
        that aren't even due yet as "arrears." Both now reuse this.
        Deliberately excludes "akan_datang" (upcoming) even if its
        due_date has technically passed — matches the pre-existing
        correct logic's distinction, not a new interpretation.

        Uses timezone.localdate(), NOT timezone.now().date() — the
        latter returns the UTC calendar date, which silently disagrees
        with the actual Asia/Jakarta (UTC+7) date for several hours
        around local midnight. Caught by a real test failure.
        """
        if self.status == self.Status.OVERDUE:
            return True
        if self.status == self.Status.PENDING:
            from django.utils import timezone
            return self.due_date < timezone.localdate()
        return False

    def save(self, *args, **kwargs):
        # Sprint 25: keep paid_at honest — auto-set the moment status
        # becomes "lunas" (first time only, so re-saving an already-paid
        # record doesn't overwrite the original payment timestamp), and
        # auto-clear it if the status is ever reverted away from "lunas"
        # (e.g. correcting a mistaken mark-as-paid). Same "don't let
        # dangling state lie" fix as Booking's CONVERTED sync, Sprint 23.
        update_fields   = kwargs.get("update_fields")
        changed_paid_at = False

        if self.status == self.Status.PAID and self.paid_at is None:
            from django.utils import timezone
            self.paid_at    = timezone.now()
            changed_paid_at = True
        elif self.status != self.Status.PAID and self.paid_at is not None:
            self.paid_at    = None
            changed_paid_at = True

        # If the caller passed a restrictive update_fields that doesn't
        # include paid_at, Django would silently skip persisting the
        # change above — make sure it's actually saved.
        if changed_paid_at and update_fields is not None and "paid_at" not in update_fields:
            kwargs["update_fields"] = list(update_fields) + ["paid_at"]

        super().save(*args, **kwargs)


# =============================================================================
# FinancialAudit — Sprint 27: the audit trail for every real-money action
# introduced in Sprints 22-26. Mirrors RequirementAudit's shape (flat
# before/after fields, nullable changed_by, silent-fail .log() classmethod)
# rather than a generic JSON snapshot — same discipline the rest of this
# codebase already trusts.
# =============================================================================

class FinancialAudit(models.Model):
    class Action(models.TextChoices):
        PAYMENT_RECORDED       = "payment_recorded",       "Pembayaran Dicatat"
        PAYMENT_STATUS_CHANGED = "payment_status_changed", "Status Pembayaran Diubah"
        PAYMENT_MARKED_OVERDUE = "payment_marked_overdue", "Pembayaran Ditandai Menunggak"
        BOOKING_CREATED        = "booking_created",         "Booking Dibuat"
        BOOKING_CANCELLED      = "booking_cancelled",       "Booking Dibatalkan"
        BOOKING_EXPIRED        = "booking_expired",         "Booking Kedaluwarsa"
        BOOKING_CONVERTED      = "booking_converted",       "Booking Dikonversi ke Penjualan"
        PRICE_CHANGED          = "price_changed",           "Harga Unit Diubah"
        KPR_ADVANCED           = "kpr_advanced",             "Status KPR Dilanjutkan"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Sprint 27 divergence from RequirementAudit: that model scopes tenant
    # isolation transitively (via requirement_status -> project). This model
    # can't do that safely — it references THREE different object types
    # (payment/booking/unit) depending on action_type, only one populated
    # per row. A direct FK is what makes the tenant-isolation regression
    # sweep simple to test and bulletproof, not an approximation of it.
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE,
        related_name="financial_audit_logs", verbose_name="Organisasi",
    )

    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)

    # Only the relevant one populated per row, same nullable-FK spirit
    # UnitPriceHistory.changed_by already uses.
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_logs",
    )
    booking = models.ForeignKey(
        "units.Booking", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_logs",
    )
    unit = models.ForeignKey(
        "units.Unit", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="financial_audit_logs",
    )

    old_value = models.CharField(max_length=50, blank=True)
    new_value = models.CharField(max_length=50, blank=True)
    notes     = models.TextField(blank=True)

    # Nullable exactly like RequirementAudit.changed_by and
    # UnitPriceHistory.changed_by — None means system-triggered
    # (mark_overdue_payments / expire_bookings). That distinction matters:
    # pretending a human "approved" a cron sweep would be dishonest, not
    # just a null-handling detail.
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="financial_audit_logs",
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Sprint 27: per-unit AR before/after, not the portfolio-wide number —
    # "this action moved THIS deal's AR from X to Y" is the meaningful
    # audit line, not the entire portfolio ticking on every payment.
    # Nullable: not every action type moves AR (e.g. a cancelled booking).
    ar_before = models.BigIntegerField(null=True, blank=True)
    ar_after  = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name        = "Audit Keuangan"
        verbose_name_plural  = "Audit Keuangan"
        ordering             = ["-changed_at"]

    def __str__(self):
        return f"[{self.get_action_display()}] {self.old_value} → {self.new_value}"

    @classmethod
    def log(
        cls,
        organization,
        action,
        changed_by = None,
        payment    = None,
        booking    = None,
        unit       = None,
        old_value  = "",
        new_value  = "",
        notes      = "",
        ar_before  = None,
        ar_after   = None,
    ):
        # Mirrors RequirementAudit.log()'s silent-fail try/except — an
        # audit-log write failing must never take down the real
        # payment/booking action that triggered it. The inner
        # transaction.atomic() is essential, not decorative: on
        # PostgreSQL, a failed query poisons the ENTIRE surrounding
        # transaction until something rolls back, regardless of whether
        # Python catches the exception. Without this savepoint, a
        # broken .log() call would silently break every subsequent
        # query in the same request/transaction — including the real
        # action this call is supposed to protect. Caught by a real
        # test failure, not a hypothetical.
        try:
            with transaction.atomic():
                cls.objects.create(
                    organization = organization,
                    action       = action,
                    changed_by   = changed_by,
                    payment      = payment,
                    booking      = booking,
                    unit         = unit,
                    old_value    = old_value or "",
                    new_value    = new_value or "",
                    notes        = notes or "",
                    ar_before    = ar_before,
                    ar_after     = ar_after,
                )
        except Exception:
            pass

