# =============================================================================
# === apps/construction/models.py ===
# =============================================================================
"""
DevelopIndo — Construction Phases Model
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel
from apps.units.models import Unit


class ConstructionPhase(TenantScopedModel):

    class Status(models.TextChoices):
        DONE    = "selesai",  "Selesai"
        ONGOING = "proses",   "Sedang Berjalan"
        WAITING = "menunggu", "Menunggu"

    STANDARD_PHASES = [
        (1, "Pembersihan & persiapan lahan"),
        (2, "Pekerjaan pondasi"),
        (3, "Rangka struktur"),
        (4, "Dinding struktural"),
        (5, "Pemasangan atap & waterproofing"),
        (6, "Finishing interior"),
        (7, "Selesai / serah terima"),
    ]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="phases", verbose_name="Unit")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="phase_updates", verbose_name="Diperbarui oleh",
    )

    phase_order = models.PositiveIntegerField(verbose_name="Urutan Fase")
    phase_name  = models.CharField(max_length=200, verbose_name="Nama Fase")
    phase_date  = models.CharField(max_length=50, verbose_name="Tanggal / Periode")
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WAITING, verbose_name="Status",
    )
    notes      = models.TextField(blank=True, verbose_name="Catatan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Fase Konstruksi"
        verbose_name_plural = "Fase Konstruksi"
        ordering            = ["unit", "phase_order"]
        unique_together     = ["unit", "phase_order"]

    def __str__(self):
        return f"Unit {self.unit.unit_number} — Fase {self.phase_order}: {self.phase_name}"

    def _resolve_organization(self):
        return self.unit.organization


class ConstructionPhoto(models.Model):
    """
    Left as a plain model — scoped transitively through
    ConstructionPhase -> Unit -> organization. If you ever query photos
    directly across tenants (rather than always through
    unit.phases.photos), give this the same TenantScopedModel +
    _resolve_organization (return self.phase.unit.organization)
    treatment as everything above.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phase = models.ForeignKey(
        ConstructionPhase, on_delete=models.CASCADE, related_name="photos", verbose_name="Fase",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="uploaded_photos", verbose_name="Diunggah oleh",
    )
    image       = models.ImageField(upload_to="construction_photos/%Y/%m/", verbose_name="Foto")
    caption     = models.CharField(max_length=300, blank=True, verbose_name="Keterangan")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Foto Konstruksi"
        verbose_name_plural = "Foto Konstruksi"
        ordering            = ["-uploaded_at"]

    def __str__(self):
        return f"Foto — {self.phase} ({self.uploaded_at.strftime('%d %b %Y')})"
