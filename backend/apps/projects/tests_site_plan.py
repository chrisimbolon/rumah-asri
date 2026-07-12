# =============================================================================
# === backend/apps/projects/tests_site_plan.py ===
# Site plan tests — covers Unit.map_status, SitePlan/SitePlanUnitMarker
# models, the three new views, and tenant isolation.
#
# Standalone file, not merged into your existing apps/projects/tests.py —
# same reasoning as tests_financial_audit.py: I haven't seen that file's
# real content, and editing it blind risks clobbering existing coverage.
# Django's default test discovery (test*.py) picks this up automatically.
#
# Upload tests use a REAL in-memory PNG generated via Pillow, not a fake
# stub — the whole point of these tests is proving the actual Image.open()
# + seek(0) dimension-reading fix works, not just that the view doesn't
# crash on some arbitrary bytes.
# =============================================================================
from datetime import date, timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership
from apps.payments.models import Payment
from apps.units.models import Unit

from .models import Project, SitePlan, SitePlanUnitMarker
from .views import SitePlanMarkerDetailView, SitePlanMarkerListView, SitePlanView


def _make_test_image(width=800, height=600, name="site_plan.png"):
    """A genuine, valid in-memory PNG — not a stub. Exercises the real
    Image.open()/seek(0) code path in SitePlanView.post()."""
    buf = BytesIO()
    Image.new("RGB", (width, height), color="white").save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


class SitePlanTestBase(TestCase):
    """One org, one project, three units in different payment states —
    enough to exercise every map_status branch without repeating setup."""

    def setUp(self):
        self.factory = APIRequestFactory()

        self.org = Organization.objects.create(name="PT Asri Sentosa Properti")
        self.other_org = Organization.objects.create(name="PT Kompetitor Developer")

        self.developer = CustomUser.objects.create_user(
            email="budi@asrisentosa.id", password="pass12345!",
            full_name="Budi Developer", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.developer, role="owner", is_active=True,
        )
        self.buyer_role_user = CustomUser.objects.create_user(
            email="andi@buyer.id", password="pass12345!",
            full_name="Andi Pembeli", role="buyer",
        )

        self.project = Project.objects.create(
            organization=self.org, name="Perumahan Asri Cluster A", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="36/72",
            land_area=72, building_area=36, price=500_000_000,
        )

    def _get_active_site_plan(self):
        return self.project.site_plans.filter(is_active=True).first()


class UnitMapStatusTests(SitePlanTestBase):
    """The real branching logic — highest-value tests in this file."""

    def test_tersedia_when_not_booked(self):
        self.assertEqual(self.unit.map_status, "tersedia")

    def test_booking_baru_when_booked_no_payments(self):
        self.unit.status = Unit.Status.BOOKED
        self.unit.save(update_fields=["status"])
        self.assertEqual(self.unit.map_status, "booking_baru")

    def test_cicilan_berjalan_when_partially_paid(self):
        self.unit.status = Unit.Status.BOOKED
        self.unit.save(update_fields=["status"])
        Payment.objects.create(
            unit=self.unit, payment_type="DP", due_date=date.today(),
            amount=100_000_000, status=Payment.Status.PAID,
        )
        self.assertEqual(self.unit.map_status, "cicilan_berjalan")

    def test_lunas_when_fully_paid(self):
        self.unit.status = Unit.Status.SOLD
        self.unit.save(update_fields=["status"])
        Payment.objects.create(
            unit=self.unit, payment_type="Lunas", due_date=date.today(),
            amount=500_000_000, status=Payment.Status.PAID,
        )
        self.assertEqual(self.unit.map_status, "lunas")

    def test_menunggak_from_explicit_overdue_status(self):
        self.unit.status = Unit.Status.BOOKED
        self.unit.save(update_fields=["status"])
        Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=10),
            amount=50_000_000, status=Payment.Status.OVERDUE,
        )
        self.assertEqual(self.unit.map_status, "menunggak")

    def test_menunggak_from_pending_past_due_date(self):
        """Same is_overdue definition Sprint 25 established — a PENDING
        payment past its due_date counts as overdue even without the
        stored status having been flipped by the cron sweep yet."""
        self.unit.status = Unit.Status.BOOKED
        self.unit.save(update_fields=["status"])
        Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=3),
            amount=50_000_000, status=Payment.Status.PENDING,
        )
        self.assertEqual(self.unit.map_status, "menunggak")

    def test_menunggak_overrides_cicilan_berjalan(self):
        """The priority rule this whole property was designed around:
        a unit that's PARTIALLY paid AND has a separate overdue
        installment must show as menunggak, not cicilan_berjalan —
        the more urgent signal wins, by design, not by accident."""
        self.unit.status = Unit.Status.BOOKED
        self.unit.save(update_fields=["status"])
        Payment.objects.create(
            unit=self.unit, payment_type="DP", due_date=date.today() - timedelta(days=60),
            amount=100_000_000, status=Payment.Status.PAID,
        )
        Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=5),
            amount=50_000_000, status=Payment.Status.OVERDUE,
        )
        # Sanity check: this unit genuinely IS partially paid —
        # confirms the test is exercising the override, not a
        # trivially-true case where ar_outstanding == price anyway.
        self.assertTrue(0 < self.unit.ar_outstanding < self.unit.price)
        self.assertEqual(self.unit.map_status, "menunggak")

    def test_akan_datang_past_due_does_not_count_as_overdue(self):
        """Matches Payment.is_overdue's deliberate exclusion (Sprint 25)
        — akan_datang past its date is still not overdue. map_status
        must not invent a stricter interpretation than is_overdue itself."""
        self.unit.status = Unit.Status.BOOKED
        self.unit.save(update_fields=["status"])
        Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 2",
            due_date=date.today() - timedelta(days=5),
            amount=50_000_000, status=Payment.Status.UPCOMING,
        )
        self.assertEqual(self.unit.map_status, "booking_baru")


class SitePlanModelTests(SitePlanTestBase):

    def test_organization_property_resolves_transitively(self):
        site_plan = SitePlan.objects.create(
            project=self.project, image=_make_test_image(),
            image_width=800, image_height=600,
        )
        self.assertEqual(site_plan.organization, self.org)

    def test_only_one_marker_per_unit(self):
        site_plan = SitePlan.objects.create(
            project=self.project, image=_make_test_image(),
            image_width=800, image_height=600,
        )
        SitePlanUnitMarker.objects.create(
            site_plan=site_plan, unit=self.unit, points=[[0, 0], [10, 0], [10, 10]],
        )
        with self.assertRaises(Exception):
            SitePlanUnitMarker.objects.create(
                site_plan=site_plan, unit=self.unit, points=[[1, 1], [11, 1], [11, 11]],
            )


class SitePlanUploadViewTests(SitePlanTestBase):

    def test_upload_creates_active_plan_with_real_dimensions(self):
        request = self.factory.post(
            "/api/projects/x/site-plan/",
            {"image": _make_test_image(width=1024, height=768), "label": "Denah Cluster A"},
            format="multipart",
        )
        force_authenticate(request, user=self.developer)
        resp = SitePlanView.as_view()(request, pk=self.project.id)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["site_plan"]["image_width"], 1024)
        self.assertEqual(resp.data["site_plan"]["image_height"], 768)
        self.assertTrue(resp.data["site_plan"]["is_active"])

    def test_uploading_new_plan_deactivates_old_one(self):
        old = SitePlan.objects.create(
            project=self.project, image=_make_test_image(),
            image_width=800, image_height=600, is_active=True,
        )
        request = self.factory.post(
            "/api/projects/x/site-plan/",
            {"image": _make_test_image(), "label": "Revisi"},
            format="multipart",
        )
        force_authenticate(request, user=self.developer)
        SitePlanView.as_view()(request, pk=self.project.id)

        old.refresh_from_db()
        self.assertFalse(old.is_active)
        self.assertEqual(self.project.site_plans.filter(is_active=True).count(), 1)

    def test_upload_rejects_non_image_file(self):
        fake_file = SimpleUploadedFile("not_an_image.txt", b"hello world", content_type="text/plain")
        request = self.factory.post(
            "/api/projects/x/site-plan/", {"image": fake_file}, format="multipart",
        )
        force_authenticate(request, user=self.developer)
        resp = SitePlanView.as_view()(request, pk=self.project.id)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_requires_developer_or_super_admin_role(self):
        request = self.factory.post(
            "/api/projects/x/site-plan/", {"image": _make_test_image()}, format="multipart",
        )
        force_authenticate(request, user=self.buyer_role_user)
        resp = SitePlanView.as_view()(request, pk=self.project.id)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_returns_none_when_no_plan_uploaded_yet(self):
        request = self.factory.get("/api/projects/x/site-plan/")
        force_authenticate(request, user=self.developer)
        resp = SitePlanView.as_view()(request, pk=self.project.id)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data["site_plan"])


class SitePlanMarkerViewTests(SitePlanTestBase):

    def setUp(self):
        super().setUp()
        self.site_plan = SitePlan.objects.create(
            project=self.project, image=_make_test_image(),
            image_width=800, image_height=600, is_active=True,
        )

    def _post_marker(self, user, unit_id, points):
        request = self.factory.post(
            "/api/projects/x/site-plan/markers/",
            {"unit_id": str(unit_id), "points": points}, format="json",
        )
        force_authenticate(request, user=user)
        return SitePlanMarkerListView.as_view()(request, pk=self.project.id)

    def test_create_marker_success(self):
        resp = self._post_marker(self.developer, self.unit.id, [[10, 10], [50, 10], [50, 50], [10, 50]])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["marker"]["unit_number"], "A-01")
        self.assertEqual(resp.data["marker"]["map_status"], "tersedia")

    def test_create_marker_rejects_fewer_than_3_points(self):
        resp = self._post_marker(self.developer, self.unit.id, [[10, 10], [50, 10]])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_marker_rejects_duplicate_unit(self):
        self._post_marker(self.developer, self.unit.id, [[10, 10], [50, 10], [50, 50]])
        resp = self._post_marker(self.developer, self.unit.id, [[1, 1], [2, 1], [2, 2]])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SitePlanUnitMarker.objects.filter(unit=self.unit).count(), 1)

    def test_create_marker_fails_without_active_site_plan(self):
        self.site_plan.delete()
        resp = self._post_marker(self.developer, self.unit.id, [[10, 10], [50, 10], [50, 50]])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_marker_requires_permission(self):
        resp = self._post_marker(self.buyer_role_user, self.unit.id, [[10, 10], [50, 10], [50, 50]])
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_marker_success(self):
        marker = SitePlanUnitMarker.objects.create(
            site_plan=self.site_plan, unit=self.unit, points=[[0, 0], [10, 0], [10, 10]],
        )
        request = self.factory.delete("/api/projects/x/site-plan/markers/y/")
        force_authenticate(request, user=self.developer)
        resp = SitePlanMarkerDetailView.as_view()(request, pk=self.project.id, marker_id=marker.id)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(SitePlanUnitMarker.objects.filter(id=marker.id).count(), 0)


class SitePlanTenantIsolationTests(SitePlanTestBase):
    """Same rigor as every other model this engagement — Org B must
    never read, upload to, or modify Org A's site plan/markers."""

    def setUp(self):
        super().setUp()
        self.other_developer = CustomUser.objects.create_user(
            email="citra@kompetitor.id", password="pass12345!",
            full_name="Citra Developer", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.other_org, user=self.other_developer, is_active=True,
        )
        self.site_plan = SitePlan.objects.create(
            project=self.project, image=_make_test_image(),
            image_width=800, image_height=600, is_active=True,
        )
        self.marker = SitePlanUnitMarker.objects.create(
            site_plan=self.site_plan, unit=self.unit, points=[[0, 0], [10, 0], [10, 10]],
        )

    def test_org_b_cannot_view_org_a_site_plan(self):
        request = self.factory.get("/api/projects/x/site-plan/")
        force_authenticate(request, user=self.other_developer)
        resp = SitePlanView.as_view()(request, pk=self.project.id)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_org_b_cannot_upload_to_org_a_project(self):
        request = self.factory.post(
            "/api/projects/x/site-plan/", {"image": _make_test_image()}, format="multipart",
        )
        force_authenticate(request, user=self.other_developer)
        resp = SitePlanView.as_view()(request, pk=self.project.id)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_org_b_cannot_list_org_a_markers(self):
        request = self.factory.get("/api/projects/x/site-plan/markers/")
        force_authenticate(request, user=self.other_developer)
        resp = SitePlanMarkerListView.as_view()(request, pk=self.project.id)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_org_b_cannot_delete_org_a_marker(self):
        request = self.factory.delete("/api/projects/x/site-plan/markers/y/")
        force_authenticate(request, user=self.other_developer)
        resp = SitePlanMarkerDetailView.as_view()(request, pk=self.project.id, marker_id=self.marker.id)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(SitePlanUnitMarker.objects.filter(id=self.marker.id).count(), 1)
