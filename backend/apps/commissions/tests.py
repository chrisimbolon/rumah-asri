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

from .models import Commission, CommissionPolicy


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
