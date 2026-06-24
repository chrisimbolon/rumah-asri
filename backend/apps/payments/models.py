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

