# =============================================================================
# === apps/documents/models.py ===
# =============================================================================
"""
RumahAsri — Documents Model
"""
from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel
from apps.units.models import Unit


class Document(TenantScopedModel):

    class Status(models.TextChoices):
        AVAILABLE  = "tersedia", "Tersedia"
        PROCESSING = "proses",   "Sedang Diproses"
        WAITING    = "menunggu", "Belum Tersedia"

    class DocType(models.TextChoices):
        PPJB     = "ppjb",     "PPJB — Perjanjian Pengikatan Jual Beli"
        IMB      = "imb",      "IMB — Izin Mendirikan Bangunan"
        AJB      = "ajb",      "Sertifikat Tanah (AJB)"
        INVOICE  = "invoice",  "Faktur Pajak PPN"
        HANDOVER = "handover", "Berita Acara Serah Terima"
        OTHER    = "other",    "Dokumen Lainnya"

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="documents", verbose_name="Unit")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="uploaded_documents", verbose_name="Diunggah oleh",
    )

    doc_type    = models.CharField(max_length=20, choices=DocType.choices, verbose_name="Tipe Dokumen")
    name        = models.CharField(max_length=300, verbose_name="Nama Dokumen")
    file        = models.FileField(upload_to="documents/%Y/%m/", null=True, blank=True, verbose_name="File")
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WAITING, verbose_name="Status",
    )
    issued_date = models.CharField(max_length=50, blank=True, verbose_name="Tanggal Terbit")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Dokumen"
        verbose_name_plural = "Dokumen"
        ordering            = ["unit", "doc_type"]

    def __str__(self):
        return f"Unit {self.unit.unit_number} — {self.get_doc_type_display()}"

    def _resolve_organization(self):
        return self.unit.organization
