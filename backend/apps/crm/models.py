# =============================================================================
# === backend/apps/crm/models.py ===
# CRM Foundation Sprint 1: Prospect, minimal.
# =============================================================================
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TenantScopedModel
from apps.projects.models import Project
from apps.units.models import Booking


class Prospect(TenantScopedModel):
    """
    A lead who hasn't committed to a unit yet. Deliberately NOT a
    CustomUser — most prospects never convert, and creating a real
    user account for every dead lead would pollute the user table.
    Conversion (Sprint 2) means linking to an existing Booking, never
    creating a user.

    Cardinality note: `interested_project` is a plain ForeignKey, not
    OneToOne — a real prospect plausibly gets quoted on more than one
    project before committing. Same reasoning as SitePlan's Project
    cardinality decision: cheap to narrow later with application-level
    validation if one-per-prospect turns out to always be true,
    expensive to widen later if wrongly locked down now.
    """

    class Status(models.TextChoices):
        BARU      = "baru",      "Baru"
        FOLLOW_UP = "follow_up", "Follow Up"
        HILANG    = "hilang",    "Hilang"
        KONVERSI  = "konversi",  "Konversi"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name   = models.CharField(max_length=200, verbose_name="Nama")
    phone  = models.CharField(max_length=20, verbose_name="Nomor Telepon")
    source = models.CharField(
        max_length=100, blank=True, verbose_name="Sumber",
        help_text="Referral, walk-in, WhatsApp, dst — free text for now, "
                   "not an enum (see Phase 2: lead-source analytics).",
    )

    interested_project = models.ForeignKey(
        Project, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="prospects",
        verbose_name="Proyek Diminati",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_prospects",
        # Enforced at form/admin/serializer-validation level, not the
        # DB — same limitation Unit.buyer's limit_choices_to already
        # lives with in this codebase. A future ProspectSerializer
        # should still validate role explicitly, not rely on this alone.
        limit_choices_to=Q(role="developer") | Q(role="agent"),
        verbose_name="Ditugaskan Kepada",
    )

    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.BARU, verbose_name="Status",
    )
    next_followup_date = models.DateField(
        null=True, blank=True, verbose_name="Tanggal Follow-up Berikutnya",
    )
    notes = models.TextField(blank=True, verbose_name="Catatan")

    # Sprint 2 reads/writes this field but does NOT add it — living
    # here from Sprint 1 is what makes Sprint 2 a genuine 0-migration
    # change. Deliberately NOT in FinancialAudit's scope (see CRM
    # roadmap intro): a conversion is a sales-pipeline event, not a
    # financial one — no money changes hands, no AR moves.
    converted_booking = models.OneToOneField(
        Booking, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="prospect",
        verbose_name="Booking Hasil Konversi",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Prospect"
        verbose_name_plural  = "Prospects"
        ordering             = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def _resolve_organization(self):
        """
        Mirrors Unit's pattern: derive org from the parent relation
        when one is present. Unlike Unit, that parent is optional here
        — a prospect can exist before any project interest is logged
        — so when interested_project is absent, organization must be
        set explicitly by the caller, same requirement Project itself
        already has (see ProjectCreateSerializer.create()).
        """
        if self.interested_project_id:
            return self.interested_project.organization
        return None
