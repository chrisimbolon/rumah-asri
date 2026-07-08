# =============================================================================
# === backend/apps/payments/tests_financial_audit.py ===
# Sprint 27: FinancialAudit tests.
#
# Written as a STANDALONE new file, not merged into your existing
# apps/payments/tests.py or apps/units/tests.py — I haven't seen the
# actual content of either, and editing files blind risks silently
# clobbering existing coverage. Django's test runner picks this up
# automatically (default discovery pattern is "test*.py", which this
# filename matches) — no wiring needed, just drop it in
# apps/payments/tests_financial_audit.py and run as normal.
#
# NOTE — verified against the real apps/core/models.py,
# apps/organizations/models.py, and apps/authentication/models.py:
#   - TenantScopedModel.organization is a real FK field (not a computed
#     property under a different name) — payment.organization,
#     unit.organization, booking.organization all work as written.
#   - The join model is OrganizationMembership, not Membership — this
#     was wrong in the first draft, fixed after checking the real file.
#   - CustomUser.objects.create_user(email=, password=, **extra_fields)
#     confirmed correct — full_name/role pass through extra_fields.
# =============================================================================
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.organizations.models import OrganizationMembership, Organization
from apps.payments.models import FinancialAudit, Payment
from apps.payments.views import PaymentDetailView, PaymentListView
from apps.projects.models import Project
from apps.units.models import Booking, Unit
from apps.units.views import BookingCancelView, BookingKPRUpdateView, UnitBookingView

User = get_user_model()


class FinancialAuditTestBase(TestCase):
    """Shared setup: one organization, one developer, one buyer, one
    project, one available unit. Individual tests build on top of this."""

    def setUp(self):
        self.factory = APIRequestFactory()

        self.org = Organization.objects.create(name="PT Asri Sentosa Properti")
        self.other_org = Organization.objects.create(name="PT Kompetitor Developer")

        self.developer = User.objects.create_user(
            email="budi@asrisentosa.id", password="testpass123",
            full_name="Budi Developer", role="developer",
        )
        OrganizationMembership.objects.create(user=self.developer, organization=self.org, is_active=True)

        self.buyer = User.objects.create_user(
            email="andi@buyer.id", password="testpass123",
            full_name="Andi Pembeli", role="buyer",
        )

        self.project = Project.objects.create(
            name="Perumahan Asri Cluster A", location="Jambi", organization=self.org,
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="36/72",
            land_area=72, building_area=36, price=500_000_000,
        )


class UnitArOutstandingTests(FinancialAuditTestBase):
    """Sprint 27: the property FinancialAudit's before/after fields rely on."""

    def test_ar_outstanding_equals_price_with_no_payments(self):
        self.assertEqual(self.unit.ar_outstanding, 500_000_000)

    def test_ar_outstanding_reduced_by_paid_payments_only(self):
        Payment.objects.create(
            unit=self.unit, payment_type="DP", due_date=date.today(),
            amount=100_000_000, status=Payment.Status.PAID,
        )
        # A pending payment must NOT reduce AR — only "lunas" counts.
        Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1", due_date=date.today() + timedelta(days=30),
            amount=50_000_000, status=Payment.Status.PENDING,
        )
        self.assertEqual(self.unit.ar_outstanding, 400_000_000)

    def test_ar_outstanding_zero_when_fully_paid(self):
        Payment.objects.create(
            unit=self.unit, payment_type="Lunas", due_date=date.today(),
            amount=500_000_000, status=Payment.Status.PAID,
        )
        self.assertEqual(self.unit.ar_outstanding, 0)


class FinancialAuditLogClassmethodTests(FinancialAuditTestBase):
    """Direct tests of FinancialAudit.log() itself, independent of any view."""

    def test_log_creates_entry_with_all_fields(self):
        FinancialAudit.log(
            organization=self.org, action=FinancialAudit.Action.PRICE_CHANGED,
            changed_by=self.developer, unit=self.unit,
            old_value="Rp 500.000.000", new_value="Rp 520.000.000",
            ar_before=500_000_000, ar_after=520_000_000,
        )
        entry = FinancialAudit.objects.get()
        self.assertEqual(entry.action, FinancialAudit.Action.PRICE_CHANGED)
        self.assertEqual(entry.changed_by, self.developer)
        self.assertEqual(entry.ar_before, 500_000_000)
        self.assertEqual(entry.ar_after, 520_000_000)

    def test_log_allows_null_changed_by_for_system_actions(self):
        """Honesty check: a system-triggered entry must NOT silently
        attribute the action to a human."""
        FinancialAudit.log(
            organization=self.org, action=FinancialAudit.Action.BOOKING_EXPIRED,
            changed_by=None, unit=self.unit,
        )
        entry = FinancialAudit.objects.get()
        self.assertIsNone(entry.changed_by)

    def test_log_never_raises_on_bad_input(self):
        """Mirrors RequirementAudit.log()'s silent-fail contract — an
        audit-log failure must never propagate and break the real action."""
        try:
            FinancialAudit.log(
                organization=None,  # organization is required at the DB level — should fail silently
                action=FinancialAudit.Action.PAYMENT_RECORDED,
            )
        except Exception as e:
            self.fail(f"FinancialAudit.log() raised {e!r} instead of failing silently")
        self.assertEqual(FinancialAudit.objects.count(), 0)


class PaymentAuditTriggerTests(FinancialAuditTestBase):
    """Sprint 27: payment_recorded + payment_status_changed."""

    def test_payment_recorded_creates_audit_entry(self):
        request = self.factory.post("/api/payments/", {
            "unit": str(self.unit.id), "payment_type": "DP",
            "due_date": str(date.today()), "amount": 100_000_000,
            "status": Payment.Status.PENDING,
        }, format="json")
        force_authenticate(request, user=self.developer)
        PaymentListView.as_view()(request)

        entry = FinancialAudit.objects.get(action=FinancialAudit.Action.PAYMENT_RECORDED)
        self.assertEqual(entry.changed_by, self.developer)
        self.assertEqual(entry.unit, self.unit)
        self.assertEqual(entry.ar_before, entry.ar_after)  # PENDING payment: no AR movement yet

    def test_payment_recorded_as_paid_moves_ar_immediately(self):
        request = self.factory.post("/api/payments/", {
            "unit": str(self.unit.id), "payment_type": "DP",
            "due_date": str(date.today()), "amount": 100_000_000,
            "status": Payment.Status.PAID,
        }, format="json")
        force_authenticate(request, user=self.developer)
        PaymentListView.as_view()(request)

        entry = FinancialAudit.objects.get(action=FinancialAudit.Action.PAYMENT_RECORDED)
        self.assertEqual(entry.ar_before, 500_000_000)
        self.assertEqual(entry.ar_after, 400_000_000)

    def test_payment_status_change_creates_audit_entry(self):
        payment = Payment.objects.create(
            unit=self.unit, payment_type="DP", due_date=date.today(),
            amount=100_000_000, status=Payment.Status.PENDING,
        )
        request = self.factory.put(
            f"/api/payments/{payment.id}/", {"status": Payment.Status.PAID}, format="json",
        )
        force_authenticate(request, user=self.developer)
        PaymentDetailView.as_view()(request, pk=payment.id)

        entry = FinancialAudit.objects.get(action=FinancialAudit.Action.PAYMENT_STATUS_CHANGED)
        self.assertEqual(entry.old_value, Payment.Status.PENDING)
        self.assertEqual(entry.new_value, Payment.Status.PAID)
        self.assertEqual(entry.ar_before, 500_000_000)
        self.assertEqual(entry.ar_after, 400_000_000)

    def test_payment_edit_without_status_change_does_not_log(self):
        """A PUT that only edits notes/bank shouldn't create a
        financial-state audit entry — only real status transitions do."""
        payment = Payment.objects.create(
            unit=self.unit, payment_type="DP", due_date=date.today(),
            amount=100_000_000, status=Payment.Status.PENDING, bank="BCA",
        )
        request = self.factory.put(
            f"/api/payments/{payment.id}/", {"bank": "Mandiri"}, format="json",
        )
        force_authenticate(request, user=self.developer)
        PaymentDetailView.as_view()(request, pk=payment.id)

        self.assertEqual(
            FinancialAudit.objects.filter(action=FinancialAudit.Action.PAYMENT_STATUS_CHANGED).count(), 0,
        )


class BookingAuditTriggerTests(FinancialAuditTestBase):
    """Sprint 27: booking_created, booking_cancelled, kpr_advanced."""

    def test_booking_created_creates_audit_entry_with_stable_ar(self):
        request = self.factory.post(f"/api/units/{self.unit.id}/book/", {
            "buyer_id": str(self.buyer.id), "booking_fee": 20_000_000,
            "booking_date": str(date.today()),
        }, format="json")
        force_authenticate(request, user=self.developer)
        UnitBookingView.as_view()(request, pk=self.unit.id)

        entry = FinancialAudit.objects.get(action=FinancialAudit.Action.BOOKING_CREATED)
        self.assertEqual(entry.changed_by, self.developer)
        # Booking a unit doesn't move AR — only a real Payment does.
        self.assertEqual(entry.ar_before, entry.ar_after)

    def test_booking_cancelled_creates_audit_entry(self):
        booking = Booking.objects.create(
            unit=self.unit, buyer=self.buyer, organization=self.org,
            spr_number="SPR-TEST-2026-001", booking_fee=20_000_000,
            booking_date=date.today(), created_by=self.developer,
        )
        self.unit.status = Unit.Status.BOOKED
        self.unit.buyer  = self.buyer
        self.unit.save(update_fields=["status", "buyer"])

        request = self.factory.post(
            f"/api/bookings/{booking.id}/cancel/", {"reason": "Buyer mundur"}, format="json",
        )
        force_authenticate(request, user=self.developer)
        BookingCancelView.as_view()(request, booking_id=booking.id)

        entry = FinancialAudit.objects.get(action=FinancialAudit.Action.BOOKING_CANCELLED)
        self.assertEqual(entry.new_value, Booking.BookingStatus.CANCELLED)
        self.assertEqual(entry.notes, "Buyer mundur")

    def test_kpr_advanced_creates_audit_entry(self):
        booking = Booking.objects.create(
            unit=self.unit, buyer=self.buyer, organization=self.org,
            spr_number="SPR-TEST-2026-002", booking_fee=20_000_000,
            booking_date=date.today(), created_by=self.developer,
        )
        request = self.factory.put(
            f"/api/units/bookings/{booking.id}/kpr/",
            {"kpr_status": Booking.KPRStatus.DIAJUKAN}, format="json",
        )
        force_authenticate(request, user=self.developer)
        BookingKPRUpdateView.as_view()(request, booking_id=booking.id)

        entry = FinancialAudit.objects.get(action=FinancialAudit.Action.KPR_ADVANCED)
        self.assertEqual(entry.old_value, Booking.KPRStatus.BELUM_DIAJUKAN)
        self.assertEqual(entry.new_value, Booking.KPRStatus.DIAJUKAN)


class SystemTriggeredAuditTests(FinancialAuditTestBase):
    """Sprint 27: payment_marked_overdue + booking_expired — the two
    cron-triggered actions. changed_by MUST be None on both."""

    def test_mark_overdue_payments_logs_with_no_actor(self):
        from django.core.management import call_command

        Payment.objects.create(
            unit=self.unit, payment_type="Cicilan 1",
            due_date=date.today() - timedelta(days=5),
            amount=50_000_000, status=Payment.Status.PENDING,
        )
        call_command("mark_overdue_payments")

        entry = FinancialAudit.objects.get(action=FinancialAudit.Action.PAYMENT_MARKED_OVERDUE)
        self.assertIsNone(entry.changed_by)
        self.assertEqual(entry.ar_before, entry.ar_after)  # still not "lunas" — no AR movement

    def test_expire_bookings_logs_with_no_actor(self):
        from django.core.management import call_command

        booking = Booking.objects.create(
            unit=self.unit, buyer=self.buyer, organization=self.org,
            spr_number="SPR-TEST-2026-003", booking_fee=20_000_000,
            booking_date=date.today() - timedelta(days=10),
            expires_at=timezone.now() - timedelta(days=1),
            created_by=self.developer,
        )
        self.unit.status = Unit.Status.BOOKED
        self.unit.buyer  = self.buyer
        self.unit.save(update_fields=["status", "buyer"])

        call_command("expire_bookings")

        entry = FinancialAudit.objects.get(action=FinancialAudit.Action.BOOKING_EXPIRED)
        self.assertIsNone(entry.changed_by)
        self.assertEqual(entry.booking, booking)


class FinancialAuditTenantIsolationTests(FinancialAuditTestBase):
    """Sprint 27: the tenant-isolation rigor the roadmap explicitly calls
    for. FinancialAudit carries organization directly (not transitively,
    unlike RequirementAudit) specifically so this is straightforward and
    bulletproof to test."""

    def setUp(self):
        super().setUp()
        self.other_developer = User.objects.create_user(
            email="citra@kompetitor.id", password="testpass123",
            full_name="Citra Developer", role="developer",
        )
        OrganizationMembership.objects.create(
            user=self.other_developer, organization=self.other_org, is_active=True,
        )
        self.other_project = Project.objects.create(
            name="Griya Kompetitor", location="Palembang", organization=self.other_org,
        )
        self.other_unit = Unit.objects.create(
            project=self.other_project, unit_number="B-01", unit_type="45/90",
            land_area=90, building_area=45, price=700_000_000,
        )

    def test_audit_entries_scoped_to_own_organization_only(self):
        FinancialAudit.log(
            organization=self.org, action=FinancialAudit.Action.PRICE_CHANGED,
            changed_by=self.developer, unit=self.unit,
        )
        FinancialAudit.log(
            organization=self.other_org, action=FinancialAudit.Action.PRICE_CHANGED,
            changed_by=self.other_developer, unit=self.other_unit,
        )

        org_entries       = FinancialAudit.objects.filter(organization=self.org)
        other_org_entries = FinancialAudit.objects.filter(organization=self.other_org)

        self.assertEqual(org_entries.count(), 1)
        self.assertEqual(other_org_entries.count(), 1)
        self.assertNotIn(other_org_entries.first(), org_entries)

    def test_payment_recorded_via_view_never_leaks_across_orgs(self):
        """End-to-end: a developer from org A recording a payment must
        only ever produce an audit entry attributed to org A, even
        though FinancialAudit as a table holds every org's rows."""
        request = self.factory.post("/api/payments/", {
            "unit": str(self.unit.id), "payment_type": "DP",
            "due_date": str(date.today()), "amount": 50_000_000,
            "status": Payment.Status.PAID,
        }, format="json")
        force_authenticate(request, user=self.developer)
        PaymentListView.as_view()(request)

        self.assertEqual(FinancialAudit.objects.filter(organization=self.org).count(), 1)
        self.assertEqual(FinancialAudit.objects.filter(organization=self.other_org).count(), 0)
