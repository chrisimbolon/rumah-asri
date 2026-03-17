"""
RumahAsri — Construction Phases Model
"""

import uuid
from django.db import models
from django.conf import settings
from apps.units.models import Unit


class ConstructionPhase(models.Model):

    class Status(models.TextChoices):
        DONE    = "selesai",  "Selesai"
        ONGOING = "proses",   "Sedang Berjalan"
        WAITING = "menunggu", "Menunggu"

    # ── Standard phases — order matters!! ─────────────────────
    STANDARD_PHASES = [
        (1, "Pembersihan & persiapan lahan"),
        (2, "Pekerjaan pondasi"),
        (3, "Rangka struktur"),
        (4, "Dinding struktural"),
        (5, "Pemasangan atap & waterproofing"),
        (6, "Finishing interior"),
        (7, "Selesai / serah terima"),
    ]

    # ── Core fields ───────────────────────────────────────────
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit        = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="phases",
        verbose_name="Unit",
    )
    updated_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="phase_updates",
        verbose_name="Diperbarui oleh",
    )

    # ── Phase details ─────────────────────────────────────────
    phase_order = models.PositiveIntegerField(verbose_name="Urutan Fase")
    phase_name  = models.CharField(max_length=200,  verbose_name="Nama Fase")
    phase_date  = models.CharField(max_length=50,   verbose_name="Tanggal / Periode")
    status      = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
        verbose_name="Status",
    )
    notes       = models.TextField(blank=True, verbose_name="Catatan")

    # ── Timestamps ────────────────────────────────────────────
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Fase Konstruksi"
        verbose_name_plural = "Fase Konstruksi"
        ordering            = ["unit", "phase_order"]
        unique_together     = ["unit", "phase_order"]

    def __str__(self):
        return f"Unit {self.unit.unit_number} — Fase {self.phase_order}: {self.phase_name}"


class ConstructionPhoto(models.Model):
    """Photos uploaded for each construction phase"""

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phase       = models.ForeignKey(
        ConstructionPhase,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="Fase",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_photos",
        verbose_name="Diunggah oleh",
    )
    image       = models.ImageField(
        upload_to="construction_photos/%Y/%m/",
        verbose_name="Foto",
    )
    caption     = models.CharField(max_length=300, blank=True, verbose_name="Keterangan")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Foto Konstruksi"
        verbose_name_plural = "Foto Konstruksi"
        ordering            = ["-uploaded_at"]

    def __str__(self):
        return f"Foto — {self.phase} ({self.uploaded_at.strftime('%d %b %Y')})"
