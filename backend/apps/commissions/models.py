# =============================================================================
# === backend/apps/commissions/models.py ===
# Commission Foundation Sprint 1: flat-rate commissions only.
# =============================================================================
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TenantScopedModel
from apps.units.models import Booking


class CommissionPolicy(TenantScopedModel):
    """
    One row per organization, configuring how commissions get
    computed for that org's sales. Decision 3 (CRM Foundation Phase B
    roadmap): rate structure differs per company — this model exists
    specifically so nothing is hardcoded platform-wide.

    Deliberately ONE policy per org this sprint — not per-project,
    not per-agent. If real usage shows a need for more granular
    policies, that's a real future sprint, not assumed here.
    """

    class RateType(models.TextChoices):
        PERCENTAGE  = "percentage",   "Persentase"
        FLAT_AMOUNT = "flat_amount",  "Nominal Tetap"
        # "tiered" is Sprint 2's addition — deliberately absent here
        # so a policy can never be set to a rate_type this sprint
        # doesn't know how to compute.

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    rate_type = models.CharField(
        max_length=20, choices=RateType.choices,
        default=RateType.PERCENTAGE, verbose_name="Jenis Tarif",
    )
    rate_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0"),
        verbose_name="Nilai Tarif",
        help_text="Persentase (mis. 2.5 untuk 2.5%) atau nominal Rupiah "
                   "tetap, tergantung Jenis Tarif.",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Commission Policy"
        verbose_name_plural  = "Commission Policies"
        constraints = [
            models.UniqueConstraint(fields=["organization"], name="one_commission_policy_per_org"),
        ]

    def __str__(self):
        return f"{self.organization} — {self.get_rate_type_display()} {self.rate_value}"

    def compute_amount(self, sale_price):
        """
        Sprint 1: flat rate only. Sprint 2 extends this for
        rate_type=tiered — kept as a single method so the booking
        hook's call site never needs to know which rate_type is
        active, only that this method exists and returns a Decimal.
        """
        if self.rate_type == self.RateType.PERCENTAGE:
            return (Decimal(sale_price) * self.rate_value / Decimal("100")).quantize(Decimal("1"))
        elif self.rate_type == self.RateType.FLAT_AMOUNT:
            return self.rate_value
        raise ValueError(f"Unknown rate_type: {self.rate_type}")


class Commission(TenantScopedModel):
    """
    One row per sale where a real agent is credited. Deliberately NOT
    created for every booking — only when Prospect.assigned_to exists
    at conversion time (see the conditional hook in
    apps.units.views.UnitBookingView.post()). A walk-in sale with no
    Prospect has no agent to pay by definition.

    `amount` is computed and SNAPSHOTTED at creation time from the
    org's CommissionPolicy — never live-recalculated. Same discipline
    FinancialAudit already uses for ar_before/ar_after: if the policy
    changes later, already-computed commissions don't silently change
    value.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        EARNED  = "earned",  "Earned"
        PAID    = "paid",    "Paid"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE,
        related_name="commission",
        verbose_name="Booking",
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="commissions",
        verbose_name="Agen",
    )
    amount = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Nominal Komisi",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.PENDING, verbose_name="Status",
    )
    computed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Commission"
        verbose_name_plural  = "Commissions"
        ordering             = ["-computed_at"]

    def __str__(self):
        return f"{self.agent.full_name} — Rp {self.amount:,.0f} ({self.get_status_display()})"

    def _resolve_organization(self):
        return self.booking.organization
