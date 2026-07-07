# =============================================================================
# === apps/payments/models.py ===
# =============================================================================
"""
DevelopIndo — Payments Model
"""
from django.db import models

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

