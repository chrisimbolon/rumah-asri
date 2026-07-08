# =============================================================================
# === backend/apps/buyer/tests.py ===
# Sprint 27: real tests for the Buyer Portal, replacing the empty
# `# Create your tests here.` scaffold that shipped all the way through
# Sprints 22-26 untouched.
#
# Important scoping note, discovered while writing this: apps/buyer/
# has no standalone Buyer model at all — Sprint 24's roadmap sketch
# ("lightweight Buyer profile, linked to Unit/NUP") was implemented
# differently in practice: buyers are CustomUser rows with role="buyer",
# referenced directly via Unit.buyer / Booking.buyer. apps/buyer/ is a
# read-only BUYER-FACING PORTAL (4 endpoints), not a data-owning app.
#
# So "tenant isolation" doesn't mean org-vs-org here (there's no
# Organization concept exposed to a buyer at all) — it means
# BUYER-vs-BUYER: can Buyer X ever see Buyer Y's unit, payments,
# timeline, or documents? That's what every test below actually checks.
#
# Deliberately NOT constructing real ConstructionPhase/Document rows —
# I haven't seen those two models' full field requirements, and
# guessing risks brittle tests for models unrelated to what Sprint 27
# is actually hardening. The isolation boundary these tests care about
# (does BuyerTimelineView/BuyerDocumentsView ever leak another buyer's
# unit_number?) is fully provable with ZERO phases/documents rows,
# since both views derive everything from get_buyer_unit(request.user)
# with no client-supplied ID anywhere in the request — there is no
# parameter available to inject a different unit through even if you
# wanted to. Worth confirming that structural fact stays true if
# either view is ever changed to accept a unit id/slug from the client.
# =============================================================================
from datetime import date, timedelta

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from django.test import TestCase

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership
from apps.payments.models import Payment
from apps.projects.models import Project
from apps.units.models import Unit

from .views import (
    BuyerDocumentsView,
    BuyerMeView,
    BuyerPaymentsView,
    BuyerTimelineView,
)

ALL_BUYER_VIEWS = [
    ("me",        BuyerMeView),
    ("timeline",  BuyerTimelineView),
    ("payments",  BuyerPaymentsView),
    ("documents", BuyerDocumentsView),
]


class BuyerPortalTestBase(TestCase):
    """
    Shared scaffolding: one organization, one project, two buyers each
    with their own unit (so cross-buyer leakage has something real to
    leak), one buyer with NO unit assigned (the 404 path), and one
    non-buyer account (the role-gate path).
    """

    def setUp(self):
        self.factory = APIRequestFactory()

        self.org = Organization.objects.create(name="PT Asri Sentosa Properti")
        self.developer = CustomUser.objects.create_user(
            email="dev@asrisentosa.id", password="pass12345!",
            full_name="Budi Developer", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.developer, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Perumahan Asri Cluster A", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )

        self.buyer_a = CustomUser.objects.create_user(
            email="andi@buyer.id", password="pass12345!",
            full_name="Andi Pembeli", role="buyer",
        )
        self.unit_a = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="36/72",
            land_area=72, building_area=36, price=500_000_000,
            buyer=self.buyer_a,
        )

        self.buyer_b = CustomUser.objects.create_user(
            email="citra@buyer.id", password="pass12345!",
            full_name="Citra Pembeli", role="buyer",
        )
        self.unit_b = Unit.objects.create(
            project=self.project, unit_number="B-02", unit_type="45/90",
            land_area=90, building_area=45, price=700_000_000,
            buyer=self.buyer_b,
        )

        # A real buyer, correctly role-tagged, but genuinely has no
        # unit assigned yet — the "hubungi developer" 404 path.
        self.buyer_no_unit = CustomUser.objects.create_user(
            email="dedi@buyer.id", password="pass12345!",
            full_name="Dedi Pembeli", role="buyer",
        )

    def _get(self, view_cls, user, **view_kwargs):
        request = self.factory.get("/api/buyer/irrelevant-for-direct-call/")
        force_authenticate(request, user=user)
        return view_cls.as_view()(request, **view_kwargs)


class BuyerRoleGateTests(BuyerPortalTestBase):
    """
    get_buyer_unit()'s `if user.role != "buyer"` check — exists in code
    since Sprint 1 of this app, never actually tested. Every buyer-portal
    endpoint must reject every non-buyer role, not just informally "work
    for buyers" by coincidence of who happens to call it.
    """

    def test_developer_blocked_from_every_buyer_endpoint(self):
        for name, view_cls in ALL_BUYER_VIEWS:
            with self.subTest(endpoint=name):
                resp = self._get(view_cls, self.developer)
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_blocked_from_every_buyer_endpoint(self):
        agent = CustomUser.objects.create_user(
            email="agen@asrisentosa.id", password="pass12345!",
            full_name="Sari Agen", role="agent",
        )
        for name, view_cls in ALL_BUYER_VIEWS:
            with self.subTest(endpoint=name):
                resp = self._get(view_cls, agent)
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_blocked_from_every_buyer_endpoint(self):
        """
        Worth pinning down explicitly: super_admin bypasses tenant
        scoping everywhere ELSE in this codebase (see
        TenantScopedQuerySet.for_user), but the buyer portal isn't a
        tenant-scoped resource at all — it's buyer-identity-scoped.
        super_admin having no assigned unit should 403, same as anyone
        else who isn't a buyer, not silently succeed because of the
        usual staff-bypass pattern.
        """
        admin = CustomUser.objects.create_user(
            email="admin@developindo.id", password="pass12345!",
            full_name="Platform Admin", role="super_admin",
        )
        for name, view_cls in ALL_BUYER_VIEWS:
            with self.subTest(endpoint=name):
                resp = self._get(view_cls, admin)
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class BuyerNoUnitAssignedTests(BuyerPortalTestBase):
    """A real buyer account, correctly role-tagged, with no Unit.buyer
    pointing at them anywhere — the honest 404, not a crash."""

    def test_every_endpoint_returns_404_with_no_unit(self):
        for name, view_cls in ALL_BUYER_VIEWS:
            with self.subTest(endpoint=name):
                resp = self._get(view_cls, self.buyer_no_unit)
                self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
                self.assertFalse(resp.data["success"])


class BuyerMeViewTests(BuyerPortalTestBase):

    def test_buyer_sees_own_unit_and_profile(self):
        resp = self._get(BuyerMeView, self.buyer_a)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["buyer"]["email"], "andi@buyer.id")
        self.assertEqual(resp.data["unit"]["unit_number"], "A-01")

    def test_buyer_b_never_sees_buyer_a_unit(self):
        resp = self._get(BuyerMeView, self.buyer_b)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["unit"]["unit_number"], "B-02")
        self.assertNotEqual(resp.data["unit"]["unit_number"], self.unit_a.unit_number)
        self.assertNotEqual(resp.data["buyer"]["email"], self.buyer_a.email)


class BuyerTimelineViewTests(BuyerPortalTestBase):
    """No ConstructionPhase rows created (see module docstring) — these
    tests prove the isolation boundary itself, not phase-data correctness."""

    def test_buyer_sees_own_unit_number_in_timeline(self):
        resp = self._get(BuyerTimelineView, self.buyer_a)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["unit_number"], "A-01")

    def test_buyer_b_timeline_never_shows_buyer_a_unit(self):
        resp = self._get(BuyerTimelineView, self.buyer_b)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["unit_number"], "B-02")


class BuyerPaymentsViewTests(BuyerPortalTestBase):
    """Real Payment rows this time — Payment is a fully-known model
    from Sprint 25's work, safe to construct with confidence."""

    def setUp(self):
        super().setUp()
        Payment.objects.create(
            unit=self.unit_a, payment_type="DP", due_date=date.today(),
            amount=100_000_000, status=Payment.Status.PAID,
        )
        Payment.objects.create(
            unit=self.unit_a, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=3),
            amount=50_000_000, status=Payment.Status.OVERDUE,
        )
        # Buyer B's own, unrelated payment — must never appear in A's totals.
        Payment.objects.create(
            unit=self.unit_b, payment_type="DP", due_date=date.today(),
            amount=999_000_000, status=Payment.Status.PAID,
        )

    def test_buyer_a_totals_only_include_own_payments(self):
        resp = self._get(BuyerPaymentsView, self.buyer_a)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total_count"], 2)
        self.assertEqual(resp.data["paid_amount"], 100_000_000)
        self.assertEqual(resp.data["overdue_count"], 1)
        # The one figure that would silently prove a leak: buyer B's
        # 999M payment must never bleed into buyer A's totals.
        self.assertEqual(resp.data["total_amount"], 150_000_000)

    def test_buyer_b_sees_only_their_own_payment(self):
        resp = self._get(BuyerPaymentsView, self.buyer_b)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total_count"], 1)
        self.assertEqual(resp.data["total_amount"], 999_000_000)


class BuyerDocumentsViewTests(BuyerPortalTestBase):
    """No Document rows created (see module docstring) — isolation
    boundary only, same reasoning as BuyerTimelineViewTests."""

    def test_buyer_sees_own_unit_number_in_documents(self):
        resp = self._get(BuyerDocumentsView, self.buyer_a)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["unit_number"], "A-01")

    def test_buyer_b_documents_never_show_buyer_a_unit(self):
        resp = self._get(BuyerDocumentsView, self.buyer_b)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["unit_number"], "B-02")