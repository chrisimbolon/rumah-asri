from datetime import date, timedelta

from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership
from apps.projects.models import Project
from apps.units.models import Unit

from .models import Payment


def _make_org_project_unit(org_name):
    """Shared setup helper — every test class in this file needs the
    same org/dev/project/unit scaffolding before it can create a
    Payment at all."""
    org = Organization.objects.create(name=org_name)
    dev = CustomUser.objects.create_user(
        email=f"dev.{org_name.lower().replace(' ', '')}@test.id",
        password="pass12345!", full_name=f"Dev {org_name}", role="developer",
    )
    OrganizationMembership.objects.create(
        organization=org, user=dev, role="owner", is_active=True,
    )
    project = Project.objects.create(
        organization=org, name=f"Cluster {org_name}", location="Jambi",
        stage=Project.Stage.CONSTRUCTION,
        start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
    )
    unit = Unit.objects.create(
        project=project, unit_number="A-01", unit_type="Tipe 45",
        land_area=90, building_area=45, price=500_000_000,
    )
    return org, dev, project, unit


# =============================================================================
# Sprint 25 — Payment & Installment Tracking
# =============================================================================
class PaymentIsOverdueTests(APITestCase):
    """
    Sprint 25: is_overdue is the single source of truth this sprint
    introduced — was previously duplicated inconsistently between
    Project._get_overdue_payments_count() (correct) and
    Project.collection_efficiency (wrong: counted not-yet-due payments
    as arrears). These tests pin down the exact, correct definition:
    menunggak, OR menunggu past its due date. Nothing else counts —
    not even akan_datang past its date, matching the pre-existing
    correct logic's deliberate exclusion.
    """

    def setUp(self):
        _, _, _, self.unit = _make_org_project_unit("Asri Sentosa Overdue")

    def test_menunggak_is_always_overdue(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=5),
            amount=10_000_000, status=Payment.Status.OVERDUE,
        )
        self.assertTrue(p.is_overdue)

    def test_menunggu_past_due_is_overdue(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=1),
            amount=10_000_000, status=Payment.Status.PENDING,
        )
        self.assertTrue(p.is_overdue)

    def test_menunggu_future_due_is_not_overdue(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() + timedelta(days=5),
            amount=10_000_000, status=Payment.Status.PENDING,
        )
        self.assertFalse(p.is_overdue)

    def test_akan_datang_past_due_is_not_overdue(self):
        """Deliberate exclusion, matches the pre-existing correct logic."""
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=5),
            amount=10_000_000, status=Payment.Status.UPCOMING,
        )
        self.assertFalse(p.is_overdue)

    def test_lunas_is_never_overdue(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=30),
            amount=10_000_000, status=Payment.Status.PAID,
        )
        self.assertFalse(p.is_overdue)

    def test_proses_bank_is_never_overdue(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=5),
            amount=10_000_000, status=Payment.Status.BANK_PROCESS,
        )
        self.assertFalse(p.is_overdue)

    def test_is_overdue_correct_at_utc_local_date_boundary(self):
        """
        Regression test for a real bug this sprint caught:
        timezone.now().date() returns the UTC calendar date, which
        silently disagrees with the actual Asia/Jakarta (UTC+7) date
        for several hours around local midnight. Deliberately
        deterministic (mocks the clock) rather than depending on what
        hour this test happens to run at — the original bug only
        showed up naturally near midnight WIB, which is exactly why it
        slipped through initially.

        17:30 UTC on the 7th = 00:30 WIB on the 8th. A payment due on
        the 7th (Jakarta-local "yesterday" at this instant) must
        register as overdue — a naive timezone.now().date() call
        would incorrectly see "the 7th" as UTC-today, not yesterday.
        """
        from datetime import datetime
        from unittest.mock import patch
        from django.utils import timezone

        fake_utc_now = timezone.make_aware(
            datetime(2026, 7, 7, 17, 30), timezone=timezone.UTC,
        )
        with patch("django.utils.timezone.now", return_value=fake_utc_now):
            p = Payment.objects.create(
                unit=self.unit, payment_type="Cicilan 1",
                due_date=date(2026, 7, 7),
                amount=10_000_000, status=Payment.Status.PENDING,
            )
            self.assertTrue(p.is_overdue)


class PaymentPaidAtSyncTests(APITestCase):
    """
    Sprint 25: paid_at auto-sync — same "don't let dangling state lie"
    fix as Booking's CONVERTED sync in Sprint 23.
    """

    def setUp(self):
        _, _, _, self.unit = _make_org_project_unit("Asri Sentosa PaidAt")

    def test_marking_lunas_sets_paid_at(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1", due_date=date.today(),
            amount=10_000_000, status=Payment.Status.PENDING,
        )
        self.assertIsNone(p.paid_at)
        p.status = Payment.Status.PAID
        p.save()
        self.assertIsNotNone(p.paid_at)

    def test_paid_at_not_overwritten_on_resave(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1", due_date=date.today(),
            amount=10_000_000, status=Payment.Status.PAID,
        )
        original_paid_at = p.paid_at
        p.bank = "BCA"
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.paid_at, original_paid_at)

    def test_reverting_from_lunas_clears_paid_at(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1", due_date=date.today(),
            amount=10_000_000, status=Payment.Status.PAID,
        )
        self.assertIsNotNone(p.paid_at)
        p.status = Payment.Status.PENDING
        p.save()
        self.assertIsNone(p.paid_at)

    def test_paid_at_persists_with_restrictive_update_fields(self):
        """
        The hardening case: calling save(update_fields=["status"])
        without "paid_at" listed must still actually persist paid_at
        to the database, not just change it in memory.
        """
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1", due_date=date.today(),
            amount=10_000_000, status=Payment.Status.PENDING,
        )
        p.status = Payment.Status.PAID
        p.save(update_fields=["status"])
        p.refresh_from_db()
        self.assertIsNotNone(p.paid_at)


class MarkOverduePaymentsCommandTests(APITestCase):
    """
    Sprint 25: is_overdue already computes this live on every access —
    this command makes the STORED status tell the truth too, so raw
    status="menunggak" filters elsewhere in the codebase don't
    silently miss genuinely-overdue payments.
    """

    def setUp(self):
        _, _, _, self.unit = _make_org_project_unit("Asri Sentosa MarkOverdue")

    def test_command_flips_pending_past_due_to_overdue(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=3),
            amount=10_000_000, status=Payment.Status.PENDING,
        )
        call_command("mark_overdue_payments")
        p.refresh_from_db()
        self.assertEqual(p.status, Payment.Status.OVERDUE)

    def test_command_ignores_future_pending(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() + timedelta(days=3),
            amount=10_000_000, status=Payment.Status.PENDING,
        )
        call_command("mark_overdue_payments")
        p.refresh_from_db()
        self.assertEqual(p.status, Payment.Status.PENDING)

    def test_command_ignores_akan_datang_even_if_past_due(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=3),
            amount=10_000_000, status=Payment.Status.UPCOMING,
        )
        call_command("mark_overdue_payments")
        p.refresh_from_db()
        self.assertEqual(p.status, Payment.Status.UPCOMING)

    def test_command_ignores_already_overdue(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=10),
            amount=10_000_000, status=Payment.Status.OVERDUE,
        )
        call_command("mark_overdue_payments")
        p.refresh_from_db()
        self.assertEqual(p.status, Payment.Status.OVERDUE)

    def test_command_ignores_lunas(self):
        p = Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=10),
            amount=10_000_000, status=Payment.Status.PAID,
        )
        call_command("mark_overdue_payments")
        p.refresh_from_db()
        self.assertEqual(p.status, Payment.Status.PAID)


class PaymentTenantIsolationTests(APITestCase):
    """
    Sprint 25: Payment already inherits TenantScopedModel and the
    views already use TenantScopedAPIView correctly (per the codebase's
    own comment about fixing "the worst bug in the codebase") — this
    is the explicit proof, same rigor as every other model this
    engagement, not just an assumption that inheritance is enough.
    """

    def setUp(self):
        self.org_a, self.dev_a, _, self.unit_a = _make_org_project_unit("Asri Sentosa Payment Isolation A")
        self.org_b, self.dev_b, _, self.unit_b = _make_org_project_unit("Org B Payment Isolation")

        self.payment_a = Payment.objects.create(
            unit=self.unit_a, payment_type="Cicilan 1", due_date=date.today(),
            amount=10_000_000, status=Payment.Status.PENDING,
        )
        self.payment_b = Payment.objects.create(
            unit=self.unit_b, payment_type="Cicilan 1", due_date=date.today(),
            amount=10_000_000, status=Payment.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_org_a_cannot_see_org_b_payments_in_list(self):
        self._login_as(self.dev_a)
        resp = self.client.get("/api/payments/")
        ids = {p["id"] for p in resp.data["results"]}
        self.assertNotIn(str(self.payment_b.id), ids)

    def test_org_a_cannot_read_org_b_payment_directly(self):
        self._login_as(self.dev_a)
        resp = self.client.get(f"/api/payments/{self.payment_b.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_org_a_cannot_update_org_b_payment(self):
        self._login_as(self.dev_a)
        resp = self.client.put(
            f"/api/payments/{self.payment_b.id}/",
            {"status": "lunas"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.payment_b.refresh_from_db()
        self.assertEqual(self.payment_b.status, Payment.Status.PENDING)