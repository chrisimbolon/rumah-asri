# =============================================================================
# === apps/core/tests.py ===
# =============================================================================
"""
Regression guard: no authenticated user should ever be able to read or
write another organization's Project, Unit, Payment, Document, or
ConstructionPhase via the dashboard endpoints, or create a Unit/Payment/
Document inside another organization's Project/Unit.

These tests map directly onto the holes found in review:
  1. PaymentDetailView had zero ownership check (read AND write).
  2. UnitDetailView fail-open for any role not explicitly handled (agent).
  3. UnitCreateSerializer let `project` be any UUID, cross-tenant or not.
  4. DocumentListView used a broken `unit__project__developer=` join chain
     and DocumentCreateSerializer had no unit ownership check at all.
  5. PhaseDetailView had zero ownership check on a WRITE path that also
     cascades into recalculating the unit's public progress percentage —
     the most severe finding in the whole audit.
  6. PaymentCreateSerializer had no unit ownership check at all — the
     same shape as #4, on the financial record creation path.

If you ever refactor TenantScopedAPIView or the manager, this file is
what should catch a regression before it reaches production.
"""
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser
from apps.construction.models import ConstructionPhase
from apps.documents.models import Document
from apps.organizations.models import Organization, OrganizationMembership
from apps.payments.models import Payment
from apps.projects.models import Project
from apps.units.models import Unit


class CrossTenantIsolationTests(APITestCase):
    def setUp(self):
        # ── Org A — the victim ──────────────────────────────────────
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
        self.document_a = Document.objects.create(
            unit=self.unit_a, doc_type="ppjb", name="PPJB Unit A-01",
        )
        self.phase_a = ConstructionPhase.objects.create(
            unit=self.unit_a, phase_order=1, phase_name="Pondasi",
            phase_date="Jan 2025", status="proses",
        )

        # ── Org B — the attacker ─────────────────────────────────────
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

    # ── Projects ───────────────────────────────────────────────────

    def test_developer_b_cannot_read_developer_a_project(self):
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/projects/{self.project_a.id}/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    # ── Units ──────────────────────────────────────────────────────

    def test_developer_b_cannot_read_developer_a_unit(self):
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/units/{self.unit_a.id}/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

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

    # ── Payments ───────────────────────────────────────────────────

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

    def test_developer_b_cannot_create_payment_for_developer_a_unit(self):
        """The PaymentCreateSerializer hole — same shape as the document one."""
        self._login_as(self.dev_b)
        resp = self.client.post("/api/payments/", {
            "unit":         str(self.unit_a.id),
            "payment_type": "Sneaky payment",
            "due_date":     "2025-03-01",
            "amount":       1,
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Documents ──────────────────────────────────────────────────

    def test_developer_b_cannot_see_developer_a_document_in_list(self):
        self._login_as(self.dev_b)
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        doc_ids = [d["id"] for d in resp.data["results"]]
        self.assertNotIn(str(self.document_a.id), doc_ids)

    def test_developer_b_cannot_create_document_for_developer_a_unit(self):
        self._login_as(self.dev_b)
        resp = self.client.post("/api/documents/", {
            "unit":     str(self.unit_a.id),
            "doc_type": "ppjb",
            "name":     "Sneaky doc",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Construction ───────────────────────────────────────────────

    def test_developer_b_cannot_update_developer_a_phase(self):
        """PhaseDetailView previously had zero check — direct cross-tenant write
        that also cascades into the unit's public progress percentage."""
        self._login_as(self.dev_b)
        resp = self.client.put(
            f"/api/construction/phases/{self.phase_a.id}/", {"status": "selesai"}, format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.phase_a.refresh_from_db()
        self.assertNotEqual(self.phase_a.status, "selesai")

    def test_developer_b_cannot_list_developer_a_unit_phases(self):
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/construction/{self.unit_a.id}/phases/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_developer_a_can_update_own_phase_and_progress_recalculates(self):
        """Sanity check the fix didn't break the actual feature."""
        self._login_as(self.dev_a)
        resp = self.client.put(
            f"/api/construction/phases/{self.phase_a.id}/", {"status": "selesai"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.unit_a.refresh_from_db()
        self.assertEqual(self.unit_a.progress, 100)

    # ── Sanity check across the board ─────────────────────────────

    def test_developer_a_can_still_read_own_data(self):
        """The fix shouldn't have broken legitimate access to any of it."""
        self._login_as(self.dev_a)

        resp = self.client.get(f"/api/projects/{self.project_a.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(f"/api/payments/{self.payment_a.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        doc_ids = [d["id"] for d in resp.data["results"]]
        self.assertIn(str(self.document_a.id), doc_ids)

        resp = self.client.get(f"/api/construction/{self.unit_a.id}/phases/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)