# =============================================================================
# === apps/projects/models.py 
# =============================================================================
"""
DevelopIndo — Projects Model
"""
from django.db import models

from apps.core.models import TenantScopedModel


class Project(TenantScopedModel):

    class Status(models.TextChoices):
        PLANNING  = "perencanaan", "Perencanaan"
        ACTIVE    = "aktif",       "Aktif"
        COMPLETED = "selesai",     "Selesai"
        ON_HOLD   = "ditunda",     "Ditunda"


    name        = models.CharField(max_length=200, verbose_name="Nama Proyek")
    location    = models.CharField(max_length=300, verbose_name="Lokasi")
    description = models.TextField(blank=True, verbose_name="Deskripsi")
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name="Status",
    )
    total_units = models.PositiveIntegerField(default=0, verbose_name="Total Unit")
    start_date  = models.DateField(verbose_name="Tanggal Mulai")
    end_date    = models.DateField(verbose_name="Target Selesai")
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
        return self.units.filter(status__in=["terjual", "proses", "serah_terima"]).count()

    @property
    def overall_progress(self):
        units = self.units.all()
        if not units.exists():
            return 0
        return round(sum(u.progress for u in units) / units.count())

    # Project has no parent relation to derive organization from — it
    # must be set explicitly (see ProjectCreateSerializer.create()).
    # _resolve_organization() intentionally not overridden — base class
    # default (returns None) applies.
