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
from apps.units.models import Booking, Unit


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
        """
        Sprint 5 (CRM Foundation Phase B): expanded from the original
        4 values. `BOOKING` deliberately does NOT exist as a separate
        status — Decision 1 resolved that "Booking" and "Won" are the
        same real event (`converted_booking IS NOT NULL`), so having
        both would let a card sit in "Booking" with no real Booking
        row behind it, the exact fiction Decision 1 exists to prevent.

        FOLLOW_UP's stored value is unchanged from the original 4-value
        enum on purpose — every existing `follow_up` row needs zero
        remapping in the Sprint 5 data migration, only baru/konversi/
        hilang do.
        """
        LEAD         = "lead",         "Lead"
        QUALIFIED    = "qualified",    "Qualified"
        FOLLOW_UP    = "follow_up",    "Follow Up"
        SITE_VISIT   = "site_visit",   "Site Visit"
        NEGOTIATION  = "negotiation",  "Negotiation"
        WON          = "won",          "Won"
        LOST         = "lost",         "Lost"

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
        default=Status.LEAD, verbose_name="Status",
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


class Activity(TenantScopedModel):
    """
    CRM Foundation Phase B, Sprint 4: follow-up history. The most-cited
    real gap from the Sansan/Joe/Suryanto review — "every call, every
    WhatsApp, every meeting, every note needs history."

    Deliberately scoped to `Prospect` only, not a generic activity log
    across every model in the platform — a generic timeline is a much
    bigger, different feature, and nothing in the feedback asked for
    one. This is Prospect follow-up history, named as such.
    """

    class ActivityType(models.TextChoices):
        CALL      = "call",      "Telepon"
        WHATSAPP  = "whatsapp",  "WhatsApp"
        MEETING   = "meeting",   "Pertemuan"
        NOTE      = "note",      "Catatan"

    prospect = models.ForeignKey(
        Prospect, on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="Prospect",
    )
    activity_type = models.CharField(
        max_length=20, choices=ActivityType.choices,
        verbose_name="Jenis Aktivitas",
    )
    notes = models.TextField(blank=True, verbose_name="Catatan")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="crm_activities",
        verbose_name="Dicatat Oleh",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Activity"
        verbose_name_plural  = "Activities"
        ordering             = ["-created_at"]

    def __str__(self):
        return f"{self.get_activity_type_display()} — {self.prospect.name}"

    def _resolve_organization(self):
        """Same pattern as Prospect._resolve_organization() — derive
        from the parent relation. Unlike Prospect, `prospect` here is
        required (never null), so this always resolves; no explicit-set
        fallback needed the way Prospect's own resolution does."""
        return self.prospect.organization


class SiteVisit(TenantScopedModel):
    """
    CRM Foundation Phase B, Sprint 6: site visit scheduling.

    Calendar-integration check (done before writing this model, not
    assumed): apps.projects.ProjectCalendarView is NOT a generic
    schedulable-event system — it's a single hardcoded query over
    ProjectRequirementStatus rows with a due_date, field names baked
    to that one purpose. Nothing to hang this off of, so SiteVisit is
    its own standalone model.

    Decided (Sprint 7 follow-up, Chris): Calendar and Site Visits stay
    deliberately separate, not merged. Calendar remains a pure
    construction-deadline tracker; site visits are a sales-pipeline
    concern, surfaced on the Prospect/Pipeline pages instead. Revisit
    only with a real, repeated request to merge them — not a default
    to reach for later.

    Relationship to Prospect.Status.SITE_VISIT (Sprint 5): the status
    is the pipeline *stage*, this row is the specific *appointment* —
    same relationship Booking already has to Unit.status. A prospect
    can be in the SITE_VISIT stage with zero, one, or several
    SiteVisit rows (reschedules happen).
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Dijadwalkan"
        COMPLETED = "completed", "Selesai"
        NO_SHOW   = "no_show",   "Tidak Hadir"
        CANCELLED = "cancelled", "Dibatalkan"

    prospect = models.ForeignKey(
        Prospect, on_delete=models.CASCADE,
        related_name="site_visits",
        verbose_name="Prospect",
    )
    # Nullable on purpose — a visit might be to a project generally,
    # before a buyer has settled on one specific unit yet. Same
    # reasoning Prospect.interested_project already uses.
    unit = models.ForeignKey(
        Unit, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="site_visits",
        verbose_name="Unit",
    )
    scheduled_at = models.DateTimeField(verbose_name="Waktu Kunjungan")
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.SCHEDULED, verbose_name="Status",
    )
    notes = models.TextField(blank=True, verbose_name="Catatan")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="crm_site_visits",
        verbose_name="Dijadwalkan Oleh",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Site Visit"
        verbose_name_plural  = "Site Visits"
        ordering             = ["scheduled_at"]

    def __str__(self):
        return f"{self.prospect.name} — {self.scheduled_at:%d %b %Y %H:%M}"

    def _resolve_organization(self):
        return self.prospect.organization

    def save(self, *args, **kwargs):
        """
        Sprint 6 convenience, same shape as UnitCreateSerializer's
        Booking-status sync (Sprint 22): scheduling a real visit is a
        real domain event, so it advances the prospect's pipeline
        stage automatically — but only forward, never backward. A
        prospect already in NEGOTIATION or further shouldn't regress
        to SITE_VISIT just because a second visit got booked.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            EARLY_STAGES = {
                Prospect.Status.LEAD,
                Prospect.Status.QUALIFIED,
                Prospect.Status.FOLLOW_UP,
            }
            if self.prospect.status in EARLY_STAGES:
                self.prospect.status = Prospect.Status.SITE_VISIT
                self.prospect.save(update_fields=["status", "updated_at"])


class CustomerProfile(TenantScopedModel):
    """
    CRM Foundation Sprint 8: real Customer entity — Decision 2 =
    Option B (Phase B roadmap).

    Auto-created (get_or_create) the moment ANY real Booking closes,
    in apps.units.views.UnitBookingView.post() — deliberately
    unconditional on prospect_id being present. A walk-in buyer with
    no CRM history is still a real customer the moment they book, not
    just ones tracked through the Prospect pipeline. This is a
    deliberate deviation from the Phase B roadmap's original wording
    ("created the moment a Prospect converts") — flagged, not silent.

    Never created through this app's own API — no POST endpoint
    exists on purpose, same "creation isn't a new trigger point"
    discipline Prospect.converted_booking already established.

    `user` is a ForeignKey, not OneToOneField — see Decision 2's
    correction in the Phase B roadmap: CustomUser accounts aren't
    scoped to a single organization (OrganizationMembership allows
    multiple), so a strict one-to-one would let two competing orgs
    share and edit the same customer record if the same person ever
    buys from both. unique_together(user, organization) gives the
    actually-intended guarantee — one profile per customer PER ORG —
    without that cross-tenant leak.

    Explicit non-goal: this model does NOT duplicate Unit, Booking, or
    Payment data. Those stay the single source of truth for their own
    facts (price, SPR, amount paid) — CustomerProfileSerializer joins
    them read-only for display; the model itself only stores what
    genuinely has nowhere else to live (family notes, budget context,
    timeline notes an agent has learned about the buyer as a person).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="customer_profiles",
        verbose_name="Pelanggan",
    )
    budget = models.BigIntegerField(
        null=True, blank=True, verbose_name="Budget",
        help_text="Perkiraan budget pelanggan dalam Rupiah (opsional).",
    )
    family_notes   = models.TextField(blank=True, verbose_name="Catatan Keluarga")
    timeline_notes = models.TextField(blank=True, verbose_name="Catatan Timeline")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Customer Profile"
        verbose_name_plural  = "Customer Profiles"
        unique_together      = [("user", "organization")]
        ordering             = ["-created_at"]

    def __str__(self):
        return f"{self.user.full_name} ({self.organization})"

    # No _resolve_organization() override — same as Project itself.
    # CustomUser has no single natural organization to derive from
    # (a buyer account can hold memberships across multiple orgs), so
    # organization must always be set explicitly by the caller, which
    # UnitBookingView.post() already does (org is already resolved
    # there from the unit being booked).
