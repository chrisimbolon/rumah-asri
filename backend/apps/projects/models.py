"""
RumahAsri — Projects Model
"""

import uuid
from django.db import models
from django.conf import settings


class Project(models.Model):

    class Status(models.TextChoices):
        PLANNING    = "perencanaan", "Perencanaan"
        ACTIVE      = "aktif",       "Aktif"
        COMPLETED   = "selesai",     "Selesai"
        ON_HOLD     = "ditunda",     "Ditunda"

    # ── Core fields ───────────────────────────────────────────
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    developer   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
        limit_choices_to={"role": "developer"},
    )
    name        = models.CharField(max_length=200, verbose_name="Nama Proyek")
    location    = models.CharField(max_length=300, verbose_name="Lokasi")
    description = models.TextField(blank=True,     verbose_name="Deskripsi")
    status      = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Status",
    )

    # ── Unit counts ───────────────────────────────────────────
    total_units = models.PositiveIntegerField(default=0, verbose_name="Total Unit")

    # ── Dates ─────────────────────────────────────────────────
    start_date  = models.DateField(verbose_name="Tanggal Mulai")
    end_date    = models.DateField(verbose_name="Target Selesai")

    # ── Timestamps ────────────────────────────────────────────
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Proyek"
        verbose_name_plural = "Proyek"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.location}"

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
        total = sum(u.progress for u in units)
        return round(total / units.count())
