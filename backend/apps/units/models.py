# =============================================================================
# === apps/units/models.py ===
# =============================================================================
"""
RumahAsri — Units Model
`organization` is denormalized directly onto Unit (not just reachable via
project) so every tenant-scoped query is a single filter, not a join
chain that's easy to forget — which is exactly what happened before:
some views used `project__developer=request.user`, others didn't.
"""
from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel
from apps.projects.models import Project


class Unit(TenantScopedModel):

    class Status(models.TextChoices):
        AVAILABLE   = "tersedia",     "Tersedia"
        IN_PROGRESS = "proses",       "Proses"
        SOLD        = "terjual",      "Terjual"
        HANDOVER    = "serah_terima", "Serah Terima"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="units", verbose_name="Proyek",
    )
    buyer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="unit", limit_choices_to={"role": "buyer"},
        verbose_name="Pembeli",
    )

    unit_number       = models.CharField(max_length=20, verbose_name="Nomor Unit")
    unit_type         = models.CharField(max_length=50, verbose_name="Tipe Unit")
    land_area         = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Luas Tanah (m²)")
    building_area     = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Luas Bangunan (m²)")
    price             = models.BigIntegerField(verbose_name="Harga (IDR)")
    status            = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name="Status",
    )
    progress          = models.PositiveIntegerField(default=0, verbose_name="Progres (%)")
    current_phase     = models.CharField(max_length=200, blank=True, verbose_name="Fase Saat Ini")
    target_completion = models.DateField(null=True, blank=True, verbose_name="Target Selesai")
    payment_method    = models.CharField(max_length=100, blank=True, verbose_name="Metode Pembayaran")
    bank              = models.CharField(max_length=50, blank=True, verbose_name="Bank")
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
