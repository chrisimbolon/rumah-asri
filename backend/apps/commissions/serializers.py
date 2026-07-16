# =============================================================================
# === backend/apps/commissions/serializers.py ===
# =============================================================================
from decimal import Decimal

from rest_framework import serializers

from .models import Commission, CommissionPolicy, CommissionTier


class CommissionTierSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CommissionTier
        fields = ["id", "policy", "min_amount", "max_amount", "rate_value"]
        read_only_fields = ["id", "policy"]

    def validate(self, attrs):
        """
        Sprint 2: reject overlapping tiers within the same policy —
        the "tier boundary correctness" this sprint's own roadmap
        note calls for. Checked here rather than left to the model,
        since the model layer has no natural place to see "every
        other tier for this policy" during a plain .create()/.save().
        """
        policy = self.instance.policy if self.instance else self.context.get("policy")
        if policy is None:
            return attrs
        min_amount = attrs.get("min_amount", getattr(self.instance, "min_amount", None))
        max_amount = attrs.get("max_amount", getattr(self.instance, "max_amount", None))

        existing = policy.tiers.all()
        if self.instance:
            existing = existing.exclude(id=self.instance.id)

        for tier in existing:
            tier_max = tier.max_amount if tier.max_amount is not None else Decimal("Infinity")
            this_max = max_amount if max_amount is not None else Decimal("Infinity")
            # Two ranges overlap unless one ends before the other starts.
            if min_amount < tier_max and tier.min_amount < this_max:
                raise serializers.ValidationError(
                    f"Rentang tumpang tindih dengan tingkat yang sudah ada "
                    f"(Rp {tier.min_amount:,.0f} – "
                    f"{'∞' if tier.max_amount is None else f'{tier.max_amount:,.0f}'})."
                )
        return attrs


class CommissionPolicySerializer(serializers.ModelSerializer):
    # Sprint 2: read-only nested tiers, so the frontend gets the
    # full picture of a tiered policy in one request. Tiers are
    # created/edited/deleted through their own dedicated endpoint,
    # never through a nested write here — nested writes in DRF are
    # exactly the kind of implicit complexity this codebase avoids.
    tiers = CommissionTierSerializer(many=True, read_only=True)

    class Meta:
        model  = CommissionPolicy
        fields = ["id", "rate_type", "rate_value", "is_active", "tiers", "created_at", "updated_at"]
        read_only_fields = ["id", "tiers", "created_at", "updated_at"]


class CommissionSerializer(serializers.ModelSerializer):
    """
    Only `status` is writable through this serializer — amount, agent,
    and booking are set once at creation (the booking hook) and never
    change afterward. A staff member can transition a commission's
    status, never edit what it's actually worth or who it's for.
    """
    agent_name     = serializers.CharField(source="agent.full_name", read_only=True)
    agent_email    = serializers.CharField(source="agent.email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    booking_spr    = serializers.CharField(source="booking.spr_number", read_only=True)
    unit_number    = serializers.CharField(source="booking.unit.unit_number", read_only=True, default=None)

    class Meta:
        model  = Commission
        fields = [
            "id", "booking", "booking_spr", "unit_number",
            "agent", "agent_name", "agent_email",
            "amount", "status", "status_display",
            "computed_at", "updated_at",
        ]
        read_only_fields = [
            "id", "booking", "booking_spr", "unit_number",
            "agent", "agent_name", "agent_email",
            "amount", "computed_at", "updated_at",
        ]
