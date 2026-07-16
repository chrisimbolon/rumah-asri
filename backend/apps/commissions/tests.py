# =============================================================================
# === backend/apps/commissions/tests.py ===
# Commission Foundation Sprint 1.
# =============================================================================
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership
from apps.projects.models import Project
from apps.units.models import Booking, Unit

from .models import Commission, CommissionPolicy, CommissionTier


class CommissionPolicyModelTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Commission")

    def test_compute_amount_percentage(self):
        policy = CommissionPolicy.objects.create(
            organization=self.org, rate_type=CommissionPolicy.RateType.PERCENTAGE,
            rate_value=Decimal("2.5"),
        )
        self.assertEqual(policy.compute_amount(500_000_000), Decimal("12500000"))

    def test_compute_amount_flat(self):
        policy = CommissionPolicy.objects.create(
            organization=self.org, rate_type=CommissionPolicy.RateType.FLAT_AMOUNT,
            rate_value=Decimal("5000000"),
        )
        # Flat amount ignores sale price entirely — same value regardless.
        self.assertEqual(policy.compute_amount(500_000_000), Decimal("5000000"))
        self.assertEqual(policy.compute_amount(1_000_000_000), Decimal("5000000"))

    def test_one_policy_per_org_enforced(self):
        CommissionPolicy.objects.create(organization=self.org)
        with self.assertRaises(Exception):
            CommissionPolicy.objects.create(organization=self.org)

    def test_default_rate_value_is_zero(self):
        """A freshly get_or_create'd policy computes zero commission
        until an admin actually sets a real rate — never a surprise
        nonzero default."""
        policy = CommissionPolicy.objects.create(organization=self.org)
        self.assertEqual(policy.compute_amount(500_000_000), Decimal("0"))


class CommissionAPITestBase(APITestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Commission API")
        self.dev = CustomUser.objects.create_user(
            email="dev.commissionapi@test.id", password="pass12345!",
            full_name="Dev Commission API", role="developer",
        )
        self.agent = CustomUser.objects.create_user(
            email="agent.commissionapi@test.id", password="pass12345!",
            full_name="Agent Commission API", role="agent",
        )
        self.other_agent = CustomUser.objects.create_user(
            email="other.agent.commissionapi@test.id", password="pass12345!",
            full_name="Other Agent Commission API", role="agent",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.agent, role="member", is_active=True,
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.commissionapi@test.id", password="pass12345!",
            full_name="Buyer Commission API", role="buyer",
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Commission API", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date="2025-01-01", end_date="2025-12-31",
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )
        self.booking = Booking.objects.create(
            unit=self.unit, buyer=self.buyer, organization=self.org,
            spr_number="SPR-TEST-COMMISSION-001", booking_fee=10_000_000,
            booking_date="2026-07-01",
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)


class CommissionPolicyAPITests(CommissionAPITestBase):

    def test_get_creates_default_policy(self):
        self._login_as(self.dev)
        resp = self.client.get("/api/commissions/policy/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["policy"]["rate_type"], "percentage")
        self.assertEqual(CommissionPolicy.objects.filter(organization=self.org).count(), 1)

    def test_developer_can_update_policy(self):
        self._login_as(self.dev)
        resp = self.client.put(
            "/api/commissions/policy/",
            {"rate_type": "percentage", "rate_value": "3.0"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        policy = CommissionPolicy.objects.get(organization=self.org)
        self.assertEqual(policy.rate_value, Decimal("3.0"))

    def test_agent_cannot_update_policy(self):
        self._login_as(self.agent)
        resp = self.client.put(
            "/api/commissions/policy/",
            {"rate_value": "99.0"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class CommissionListAPITests(CommissionAPITestBase):

    def setUp(self):
        super().setUp()
        self.commission_agent = Commission.objects.create(
            organization=self.org, booking=self.booking, agent=self.agent,
            amount=Decimal("12500000"),
        )

    def test_developer_sees_all_org_commissions(self):
        self._login_as(self.dev)
        resp = self.client.get("/api/commissions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_agent_sees_only_own_commissions(self):
        self._login_as(self.other_agent)
        resp = self.client.get("/api/commissions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_owning_agent_sees_their_commission(self):
        self._login_as(self.agent)
        resp = self.client.get("/api/commissions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_filter_by_status(self):
        self._login_as(self.dev)
        resp = self.client.get("/api/commissions/?status=earned")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)


class CommissionDetailAPITests(CommissionAPITestBase):

    def setUp(self):
        super().setUp()
        self.commission = Commission.objects.create(
            organization=self.org, booking=self.booking, agent=self.agent,
            amount=Decimal("12500000"),
        )

    def test_developer_can_transition_status(self):
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/commissions/{self.commission.id}/",
            {"status": "earned"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.commission.refresh_from_db()
        self.assertEqual(self.commission.status, Commission.Status.EARNED)

    def test_agent_cannot_self_certify_own_commission(self):
        """The specific control this design exists for: an agent
        cannot mark their own commission paid, even though they can
        view it."""
        self._login_as(self.agent)
        resp = self.client.put(
            f"/api/commissions/{self.commission.id}/",
            {"status": "paid"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.commission.refresh_from_db()
        self.assertEqual(self.commission.status, Commission.Status.PENDING)

    def test_agent_can_view_own_commission_detail(self):
        self._login_as(self.agent)
        resp = self.client.get(f"/api/commissions/{self.commission.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_other_agent_cannot_view_commission_that_is_not_theirs(self):
        self._login_as(self.other_agent)
        resp = self.client.get(f"/api/commissions/{self.commission.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_write_amount_through_payload(self):
        """amount is permanently fixed at creation — no API path
        should ever let it be edited after the fact."""
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/commissions/{self.commission.id}/",
            {"amount": "999999999", "status": "earned"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.commission.refresh_from_db()
        self.assertEqual(self.commission.amount, Decimal("12500000"))


class CommissionTenantIsolationTests(CommissionAPITestBase):

    def setUp(self):
        super().setUp()
        self.commission = Commission.objects.create(
            organization=self.org, booking=self.booking, agent=self.agent,
            amount=Decimal("12500000"),
        )
        # Fix: the org-A policy has to actually exist before a test can
        # assert it's different from org-B's — nothing else in this
        # class ever creates one otherwise.
        self.policy = CommissionPolicy.objects.create(organization=self.org)
        self.other_org = Organization.objects.create(name="Org Lain Commission Isolation")
        self.other_dev = CustomUser.objects.create_user(
            email="dev.commissionisolation.other@test.id", password="pass12345!",
            full_name="Dev Org Lain", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.other_org, user=self.other_dev, role="owner", is_active=True,
        )

    def test_org_b_cannot_see_org_a_commission_in_list(self):
        self._login_as(self.other_dev)
        resp = self.client.get("/api/commissions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_org_b_cannot_retrieve_org_a_commission_detail(self):
        self._login_as(self.other_dev)
        resp = self.client.get(f"/api/commissions/{self.commission.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_org_b_gets_own_separate_policy(self):
        self._login_as(self.other_dev)
        resp = self.client.get("/api/commissions/policy/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # self.policy (org A, created in setUp) must never be the same
        # row org B's request just got back.
        self.assertNotEqual(str(self.policy.id), resp.data["policy"]["id"])


# =============================================================================
# Sprint 2 (Commission Foundation): Tiered Rates.
# =============================================================================

class CommissionTierComputationTests(TestCase):
    """
    Tier boundary correctness — the exact thing this sprint's own
    roadmap note names as the priority. Convention: min_amount
    inclusive, max_amount exclusive, top tier open-ended.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Tiered")
        self.policy = CommissionPolicy.objects.create(
            organization=self.org, rate_type=CommissionPolicy.RateType.TIERED,
        )
        # 0 - 500M: 2%, 500M - 1B: 2.5%, 1B+: 3%
        CommissionTier.objects.create(
            organization=self.org, policy=self.policy,
            min_amount=Decimal("0"), max_amount=Decimal("500000000"),
            rate_value=Decimal("2.0"),
        )
        CommissionTier.objects.create(
            organization=self.org, policy=self.policy,
            min_amount=Decimal("500000000"), max_amount=Decimal("1000000000"),
            rate_value=Decimal("2.5"),
        )
        CommissionTier.objects.create(
            organization=self.org, policy=self.policy,
            min_amount=Decimal("1000000000"), max_amount=None,
            rate_value=Decimal("3.0"),
        )

    def test_price_in_first_tier(self):
        self.assertEqual(self.policy.compute_amount(300_000_000), Decimal("6000000"))  # 2%

    def test_price_exactly_on_lower_boundary_is_inclusive(self):
        """500M lands in the SECOND tier (min_amount inclusive),
        not the first — proves the boundary convention is real,
        not just documented."""
        amount = self.policy.compute_amount(500_000_000)
        self.assertEqual(amount, Decimal("12500000"))  # 2.5%, not 2%

    def test_price_just_below_boundary_stays_in_lower_tier(self):
        tier = self.policy.find_tier(Decimal("499999999"))
        self.assertEqual(tier.rate_value, Decimal("2.0"))

    def test_price_in_open_ended_top_tier(self):
        self.assertEqual(self.policy.compute_amount(5_000_000_000), Decimal("150000000"))  # 3%

    def test_price_with_no_covering_tier_raises(self):
        """Deliberately proves the failure mode, not just the happy
        path — a gap in tier coverage must raise loudly, never
        silently return a wrong/zero commission."""
        gapped_org = Organization.objects.create(name="Org Gapped Tiers")
        gapped_policy = CommissionPolicy.objects.create(
            organization=gapped_org, rate_type=CommissionPolicy.RateType.TIERED,
        )
        CommissionTier.objects.create(
            organization=gapped_org, policy=gapped_policy,
            min_amount=Decimal("0"), max_amount=Decimal("100"),
            rate_value=Decimal("2.0"),
        )
        with self.assertRaises(ValueError):
            gapped_policy.compute_amount(999_999_999)


class CommissionTierAPITests(CommissionAPITestBase):

    def test_developer_can_create_tier(self):
        self._login_as(self.dev)
        resp = self.client.post(
            "/api/commissions/policy/tiers/",
            {"min_amount": "0", "max_amount": "500000000", "rate_value": "2.0"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_agent_cannot_create_tier(self):
        self._login_as(self.agent)
        resp = self.client.post(
            "/api/commissions/policy/tiers/",
            {"min_amount": "0", "max_amount": "500000000", "rate_value": "2.0"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_overlapping_tier_rejected(self):
        self._login_as(self.dev)
        self.client.post(
            "/api/commissions/policy/tiers/",
            {"min_amount": "0", "max_amount": "500000000", "rate_value": "2.0"},
            format="json",
        )
        resp = self.client.post(
            "/api/commissions/policy/tiers/",
            # Overlaps the first tier's range (200M falls inside 0-500M)
            {"min_amount": "200000000", "max_amount": "700000000", "rate_value": "2.5"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adjacent_non_overlapping_tiers_accepted(self):
        """The exact edge case worth proving explicitly: two tiers
        that share a boundary (one's max_amount equals the next's
        min_amount) are NOT an overlap, given max_amount is exclusive."""
        self._login_as(self.dev)
        resp1 = self.client.post(
            "/api/commissions/policy/tiers/",
            {"min_amount": "0", "max_amount": "500000000", "rate_value": "2.0"},
            format="json",
        )
        resp2 = self.client.post(
            "/api/commissions/policy/tiers/",
            {"min_amount": "500000000", "max_amount": None, "rate_value": "2.5"},
            format="json",
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)

    def test_developer_can_delete_tier(self):
        self._login_as(self.dev)
        create_resp = self.client.post(
            "/api/commissions/policy/tiers/",
            {"min_amount": "0", "max_amount": "500000000", "rate_value": "2.0"},
            format="json",
        )
        tier_id = create_resp.data["tier"]["id"]
        resp = self.client.delete(f"/api/commissions/policy/tiers/{tier_id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(CommissionTier.objects.filter(id=tier_id).exists())


class FlatRatePolicyRegressionTests(CommissionAPITestBase):
    """
    Sprint 2's own scope note: 'no forced migration — flat-rate
    policies stay flat-rate until an org explicitly switches.' This
    proves Sprint 1's flat-rate flow is completely unaffected by
    everything Sprint 2 added.
    """

    def test_percentage_policy_still_computes_correctly(self):
        self._login_as(self.dev)
        self.client.put(
            "/api/commissions/policy/",
            {"rate_type": "percentage", "rate_value": "2.5"}, format="json",
        )
        policy = CommissionPolicy.objects.get(organization=self.org)
        self.assertEqual(policy.compute_amount(500_000_000), Decimal("12500000"))

    def test_flat_amount_policy_still_computes_correctly(self):
        self._login_as(self.dev)
        self.client.put(
            "/api/commissions/policy/",
            {"rate_type": "flat_amount", "rate_value": "5000000"}, format="json",
        )
        policy = CommissionPolicy.objects.get(organization=self.org)
        self.assertEqual(policy.compute_amount(999_999_999), Decimal("5000000"))
