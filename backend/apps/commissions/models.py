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
        TIERED      = "tiered",       "Bertingkat"
        # Sprint 2 (Commission Foundation): TIERED added. Sprint 1
        # policies already on percentage/flat_amount are completely
        # unaffected by this — no migration touches existing rows,
        # a policy only becomes tiered if an org explicitly switches.

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
        Sprint 1: flat rate (percentage / flat_amount). Sprint 2 adds
        tiered — kept as a single method so the booking hook's call
        site never needs to know which rate_type is active, only that
        this method exists and returns a Decimal.
        """
        if self.rate_type == self.RateType.PERCENTAGE:
            return (Decimal(sale_price) * self.rate_value / Decimal("100")).quantize(Decimal("1"))
        elif self.rate_type == self.RateType.FLAT_AMOUNT:
            return self.rate_value
        elif self.rate_type == self.RateType.TIERED:
            tier = self.find_tier(sale_price)
            if tier is None:
                raise ValueError(
                    f"No CommissionTier covers sale_price={sale_price} for "
                    f"policy {self.id} — tiers must cover every possible "
                    f"price, including an open-ended top tier (max_amount=None)."
                )
            return (Decimal(sale_price) * tier.rate_value / Decimal("100")).quantize(Decimal("1"))
        raise ValueError(f"Unknown rate_type: {self.rate_type}")

    def find_tier(self, sale_price):
        """
        Sprint 2. Boundary convention: min_amount inclusive, max_amount
        exclusive — same as a standard tax-bracket lookup. The top
        tier has max_amount=None (open-ended), matching anything
        >= its min_amount with no upper limit.
        """
        sale_price = Decimal(sale_price)
        for tier in self.tiers.order_by("min_amount"):
            if tier.min_amount <= sale_price and (tier.max_amount is None or sale_price < tier.max_amount):
                return tier
        return None


class CommissionTier(TenantScopedModel):
    """
    Sprint 2 (Commission Foundation): a price bracket within a
    tiered CommissionPolicy. `rate_value` here is always a
    percentage — deliberately not a flat-amount-per-tier option, to
    keep this sprint focused; if a real need for per-tier flat
    amounts ever comes up, that's a small, real follow-up, not
    assumed now.

    `max_amount` is nullable — the top tier is open-ended, matching
    everything at or above its `min_amount` with no ceiling.
    Boundary convention: min_amount inclusive, max_amount exclusive,
    same as a standard tax-bracket lookup — see
    CommissionPolicy.find_tier()'s own docstring.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    policy = models.ForeignKey(
        CommissionPolicy, on_delete=models.CASCADE,
        related_name="tiers",
        verbose_name="Kebijakan",
    )
    min_amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Batas Bawah",
    )
    max_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name="Batas Atas",
        help_text="Kosongkan untuk tingkat teratas (tanpa batas atas).",
    )
    rate_value = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Persentase Tingkat Ini",
    )

    class Meta:
        verbose_name        = "Commission Tier"
        verbose_name_plural  = "Commission Tiers"
        ordering             = ["min_amount"]

    def __str__(self):
        upper = f"{self.max_amount:,.0f}" if self.max_amount is not None else "∞"
        return f"Rp {self.min_amount:,.0f} – {upper}: {self.rate_value}%"

    def _resolve_organization(self):
        return self.policy.organization


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
        # Booking Rebooking Foundation Sprint 1: set automatically
        # when the underlying Booking gets cancelled — see
        # BookingCancelView.post()'s conditional hook. A PAID
        # commission is deliberately never auto-voided; see that
        # hook's own comment for why.
        VOID    = "void",    "Void"

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
