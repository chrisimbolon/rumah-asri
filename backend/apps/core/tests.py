# =============================================================================
# === apps/core/tests.py ===
# =============================================================================
"""
Regression guard: no authenticated user should ever be able to read or
write another organization's Project, Unit, or Payment via the detail
endpoints, or create a Unit inside another organization's Project.

These four tests map directly onto the three holes found in review:
  1. PaymentDetailView had zero ownership check (read AND write).
  2. UnitDetailView fail-open for any role not explicitly handled (agent).
  3. UnitCreateSerializer let `project` be any UUID, cross-tenant or not.

If you ever refactor TenantScopedAPIView or the manager, this file is
what should catch a regression before it reaches production.
"""
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership
from apps.payments.models import Payment
from apps.projects.models import Project
from apps.units.models import Unit


class CrossTenantIsolationTests(APITestCase):
    def setUp(self):
        # Org A — the victim
        self.org_a = Organization.objects.create(name="Asri Sentosa")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a@test.id", password="pass12345!",
            full_name="Dev A", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner",
        )
        self.project_a = Project.objects.create(
            organization=self.org_a, name="Cluster A", location="Jambi",
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit_a = Unit.objects.create(
            project=self.project_a, unit_number="A-01", unit_type="Tipe 45",
            land_area=72, building_area=45, price=850_000_000,
        )
        self.payment_a = Payment.objects.create(
            unit=self.unit_a, payment_type="DP",
            due_date=date(2025, 2, 1), amount=100_000_000,
        )

        # Org B — the attacker
        self.org_b = Organization.objects.create(name="Griya Makmur")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b@test.id", password="pass12345!",
            full_name="Dev B", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner",
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_developer_b_cannot_read_developer_a_project(self):
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/projects/{self.project_a.id}/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_developer_b_cannot_read_developer_a_unit(self):
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/units/{self.unit_a.id}/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_developer_b_cannot_read_or_write_developer_a_payment(self):
        """The PaymentDetailView hole — previously this passed straight through."""
        self._login_as(self.dev_b)

        resp = self.client.get(f"/api/payments/{self.payment_a.id}/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

        resp = self.client.put(
            f"/api/payments/{self.payment_a.id}/", {"status": "lunas"}, format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.payment_a.refresh_from_db()
        self.assertNotEqual(self.payment_a.status, "lunas")

    def test_developer_b_cannot_create_unit_in_developer_a_project(self):
        """The UnitCreateSerializer hole — previously this would have succeeded."""
        self._login_as(self.dev_b)
        resp = self.client.post("/api/units/", {
            "project":       str(self.project_a.id),
            "unit_number":   "X-99",
            "unit_type":     "Tipe 36",
            "land_area":     60,
            "building_area": 36,
            "price":         500_000_000,
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Unit.objects.filter(unit_number="X-99").exists())

    def test_developer_a_can_still_read_own_data(self):
        """Sanity check — the fix shouldn't have broken legitimate access."""
        self._login_as(self.dev_a)
        resp = self.client.get(f"/api/projects/{self.project_a.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(f"/api/payments/{self.payment_a.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
