from datetime import date, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser
from apps.commissions.models import Commission, CommissionPolicy
from apps.crm.models import CustomerProfile, Prospect
from apps.organizations.models import Organization, OrganizationMembership
from apps.projects.models import Project

from .models import Booking, Unit, UnitPriceHistory


# =============================================================================
# Sprint 22 — Unit Inventory, Realized
# =============================================================================
class UnitStatusTransitionTests(APITestCase):
    """
    Sprint 22: the transition guard. Before this fix, PUT /api/units/<id>/
    let ANY status jump happen with zero validation — a fresh 'tersedia'
    unit could be PUT straight to 'serah_terima' with no booking, no
    buyer, nothing in between. This is the exact "brakes don't work"
    problem flagged during the Seats First planning conversation,
    fixed for real here.

    Covers:
    - Legal forward transitions succeed (tersedia→dipesan→proses→terjual→serah_terima)
    - Illegal transitions are rejected with a clear message
    - Same-status "changes" (no-op) are always allowed
    - Handover is a genuine terminal state — nothing is legal after it
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Unit Transition")
        self.dev = CustomUser.objects.create_user(
            email="dev.unittransition@test.id", password="pass12345!",
            full_name="Dev Unit Transition", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Unit Transition", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_legal_transition_tersedia_to_dipesan(self):
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"status": "dipesan"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, Unit.Status.BOOKED)

    def test_illegal_transition_tersedia_to_terjual_rejected(self):
        """Cannot skip straight from available to sold — no booking, no process step."""
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"status": "terjual"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", resp.data["errors"])
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, Unit.Status.AVAILABLE)

    def test_illegal_transition_backwards_from_terjual_rejected(self):
        """Cannot revert a sold unit back to available via a manual edit."""
        self.unit.status = Unit.Status.SOLD
        self.unit.save(update_fields=["status"])

        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"status": "tersedia"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_status_noop_always_allowed(self):
        """Setting status to what it already is isn't a 'transition' at all."""
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"status": "tersedia"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_handover_is_terminal(self):
        """Nothing is legal after serah_terima — it's the end of the line."""
        self.unit.status = Unit.Status.HANDOVER
        self.unit.save(update_fields=["status"])

        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"status": "dipesan"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_legal_chain(self):
        """The entire lifecycle, one legal step at a time, all succeed."""
        self._login_as(self.dev)
        for new_status in ["dipesan", "proses", "terjual", "serah_terima"]:
            resp = self.client.put(
                f"/api/units/{self.unit.id}/", {"status": new_status}, format="json",
            )
            self.assertEqual(
                resp.status_code, status.HTTP_200_OK,
                f"Expected transitioning to '{new_status}' to succeed"
            )


class UnitPriceHistoryTests(APITestCase):
    """
    Sprint 22: append-only price change log. Written automatically on
    real price changes only — never on creation, never on a no-op PUT
    that doesn't actually touch the price field.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Price History")
        self.dev = CustomUser.objects.create_user(
            email="dev.pricehistory@test.id", password="pass12345!",
            full_name="Dev Price History", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Price History", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-02", unit_type="Tipe 60",
            land_area=120, building_area=60, price=700_000_000,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_price_change_creates_history_entry(self):
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"price": 750_000_000}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(UnitPriceHistory.objects.filter(unit=self.unit).count(), 1)
        entry = UnitPriceHistory.objects.get(unit=self.unit)
        self.assertEqual(entry.old_price, 700_000_000)
        self.assertEqual(entry.new_price, 750_000_000)
        self.assertEqual(entry.changed_by, self.dev)

    def test_no_history_entry_when_price_unchanged(self):
        """Updating some OTHER field shouldn't create a phantom history row."""
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"current_phase": "Finishing interior"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(UnitPriceHistory.objects.filter(unit=self.unit).count(), 0)

    def test_no_history_entry_on_creation(self):
        """Creating a brand new unit isn't a 'price change' — no history yet."""
        self.assertEqual(UnitPriceHistory.objects.filter(unit=self.unit).count(), 0)

    def test_multiple_price_changes_all_logged_in_order(self):
        self._login_as(self.dev)
        self.client.put(f"/api/units/{self.unit.id}/", {"price": 720_000_000}, format="json")
        self.client.put(f"/api/units/{self.unit.id}/", {"price": 690_000_000}, format="json")

        history = list(UnitPriceHistory.objects.filter(unit=self.unit).order_by("changed_at"))
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].new_price, 720_000_000)
        self.assertEqual(history[1].new_price, 690_000_000)
        self.assertEqual(history[1].old_price, 720_000_000)

    def test_price_history_exposed_in_unit_serializer(self):
        self._login_as(self.dev)
        self.client.put(f"/api/units/{self.unit.id}/", {"price": 750_000_000}, format="json")

        resp = self.client.get(f"/api/units/{self.unit.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["unit"]["price_history"]), 1)
        self.assertEqual(resp.data["unit"]["price_history"][0]["new_price"], 750_000_000)


class UnitTenantIsolationTests(APITestCase):
    """
    Sprint 22: Unit already inherits TenantScopedModel, but given how
    much rigor tenant isolation gets everywhere else in this platform,
    it earns its own explicit proof here too — not just an assumption
    that inheritance alone guarantees correctness.

    Confirmed against apps/core/views.py: TenantScopedAPIView.get_object()
    only ever raises NotFound (404) — there's no 403 path in the shared
    base class at all. The deliberately vague message ("Tidak ditemukan,
    atau Anda tidak memiliki akses.") is a nice touch too — it never
    reveals to an unauthorized caller whether the object exists in
    someone else's org or doesn't exist anywhere at all.
    """

    def setUp(self):
        self.org_a = Organization.objects.create(name="Asri Sentosa Unit Isolation A")
        self.org_b = Organization.objects.create(name="Org B Unit Isolation")

        self.dev_a = CustomUser.objects.create_user(
            email="dev.unitisolation.a@test.id", password="pass12345!",
            full_name="Dev Unit Isolation A", role="developer",
        )
        self.dev_b = CustomUser.objects.create_user(
            email="dev.unitisolation.b@test.id", password="pass12345!",
            full_name="Dev Unit Isolation B", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

        self.project_a = Project.objects.create(
            organization=self.org_a, name="Cluster Isolation A", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.project_b = Project.objects.create(
            organization=self.org_b, name="Cluster Isolation B", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit_a = Unit.objects.create(
            project=self.project_a, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )
        self.unit_b = Unit.objects.create(
            project=self.project_b, unit_number="B-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_org_a_cannot_see_org_b_units_in_list(self):
        self._login_as(self.dev_a)
        resp = self.client.get("/api/units/")
        ids = {u["id"] for u in resp.data["results"]}
        self.assertIn(str(self.unit_a.id), ids)
        self.assertNotIn(str(self.unit_b.id), ids)

    def test_org_a_cannot_read_org_b_unit_directly(self):
        self._login_as(self.dev_a)
        resp = self.client.get(f"/api/units/{self.unit_b.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_org_a_cannot_update_org_b_unit(self):
        self._login_as(self.dev_a)
        resp = self.client.put(
            f"/api/units/{self.unit_b.id}/", {"status": "dipesan"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.unit_b.refresh_from_db()
        self.assertEqual(self.unit_b.status, Unit.Status.AVAILABLE)


# =============================================================================
# Sprint 23 — NUP & Booking Flow
# =============================================================================
class BookingCreationAndExpiryTests(APITestCase):
    """
    Sprint 23: without a real deadline, a "dipesan" unit could sit
    reserved forever with zero pressure to pay the booking fee. This
    covers both the deadline actually getting set on creation, and the
    expire_bookings command correctly acting on it (and, just as
    importantly, correctly leaving everything else alone).
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Booking Expiry")
        self.dev = CustomUser.objects.create_user(
            email="dev.bookingexpiry@test.id", password="pass12345!",
            full_name="Dev Booking Expiry", role="developer",
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.bookingexpiry@test.id", password="pass12345!",
            full_name="Buyer Booking Expiry", role="buyer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Booking Expiry", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def _book_unit(self, expiry_days=None):
        payload = {
            "buyer_id": str(self.buyer.id),
            "booking_fee": 10_000_000,
        }
        if expiry_days is not None:
            payload["expiry_days"] = expiry_days
        self._login_as(self.dev)
        return self.client.post(
            f"/api/units/{self.unit.id}/book/", payload, format="json",
        )

    def test_booking_gets_a_default_expiry(self):
        resp = self._book_unit()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(resp.data["booking"]["expires_at"])

        booking = Booking.objects.get(unit=self.unit)
        self.assertIsNotNone(booking.expires_at)
        # Default is 7 days — allow a small tolerance for test execution time
        expected = timezone.now() + timedelta(days=Booking.DEFAULT_EXPIRY_DAYS)
        self.assertAlmostEqual(
            booking.expires_at.timestamp(), expected.timestamp(), delta=10
        )

    def test_custom_expiry_days_respected(self):
        resp = self._book_unit(expiry_days=14)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        booking = Booking.objects.get(unit=self.unit)
        expected = timezone.now() + timedelta(days=14)
        self.assertAlmostEqual(
            booking.expires_at.timestamp(), expected.timestamp(), delta=10
        )

    def test_expire_bookings_command_reverts_unit_and_booking(self):
        self._book_unit()
        booking = Booking.objects.get(unit=self.unit)
        # Force it into the past so the command actually finds it
        booking.expires_at = timezone.now() - timedelta(days=1)
        booking.save(update_fields=["expires_at"])

        call_command("expire_bookings")

        booking.refresh_from_db()
        self.unit.refresh_from_db()
        self.assertEqual(booking.status, Booking.BookingStatus.EXPIRED)
        self.assertEqual(self.unit.status, Unit.Status.AVAILABLE)
        self.assertIsNone(self.unit.buyer)

    def test_expire_bookings_command_leaves_non_expired_bookings_alone(self):
        self._book_unit(expiry_days=30)   # far in the future

        call_command("expire_bookings")

        booking = Booking.objects.get(unit=self.unit)
        self.unit.refresh_from_db()
        self.assertEqual(booking.status, Booking.BookingStatus.ACTIVE)
        self.assertEqual(self.unit.status, Unit.Status.BOOKED)

    def test_expire_bookings_command_ignores_already_cancelled(self):
        self._book_unit()
        booking = Booking.objects.get(unit=self.unit)
        booking.status = Booking.BookingStatus.CANCELLED
        booking.expires_at = timezone.now() - timedelta(days=1)
        booking.save(update_fields=["status", "expires_at"])

        call_command("expire_bookings")

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.BookingStatus.CANCELLED)

    def test_expire_bookings_command_ignores_already_converted(self):
        self._book_unit()
        booking = Booking.objects.get(unit=self.unit)
        booking.status = Booking.BookingStatus.CONVERTED
        booking.expires_at = timezone.now() - timedelta(days=1)
        booking.save(update_fields=["status", "expires_at"])

        call_command("expire_bookings")

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.BookingStatus.CONVERTED)

    def test_booking_with_no_expiry_never_auto_expires(self):
        """Legacy-data safety: a booking created before this field
        existed (expires_at=None) must never get swept up by the
        command, however old it is."""
        self._book_unit()
        booking = Booking.objects.get(unit=self.unit)
        booking.expires_at = None
        booking.save(update_fields=["expires_at"])

        call_command("expire_bookings")

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.BookingStatus.ACTIVE)

    def test_is_expired_property(self):
        self._book_unit()
        booking = Booking.objects.get(unit=self.unit)
        self.assertFalse(booking.is_expired)

        booking.expires_at = timezone.now() - timedelta(days=1)
        booking.save(update_fields=["expires_at"])
        self.assertTrue(booking.is_expired)


class UnitAdvanceConvertsBookingTests(APITestCase):
    """
    Sprint 23: closes the gap where advancing a Unit from dipesan to
    proses never touched the Booking record at all — leaving a
    "still ACTIVE" booking dangling for a sale that's already in
    progress.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Convert Booking")
        self.dev = CustomUser.objects.create_user(
            email="dev.convertbooking@test.id", password="pass12345!",
            full_name="Dev Convert Booking", role="developer",
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.convertbooking@test.id", password="pass12345!",
            full_name="Buyer Convert Booking", role="buyer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Convert Booking", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_advancing_to_proses_converts_active_booking(self):
        self._login_as(self.dev)
        self.client.post(
            f"/api/units/{self.unit.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000},
            format="json",
        )
        booking = Booking.objects.get(unit=self.unit)
        self.assertEqual(booking.status, Booking.BookingStatus.ACTIVE)

        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"status": "proses"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.BookingStatus.CONVERTED)

    def test_advancing_without_prior_booking_record_does_not_crash(self):
        """
        A unit can reach 'dipesan' via a direct manual PUT (not
        necessarily through the /book/ endpoint) — so no Booking row
        may exist at all. The conversion sync must handle that
        gracefully, not raise Booking.DoesNotExist.
        """
        self._login_as(self.dev)
        # Manually move to dipesan WITHOUT going through /book/ —
        # legal per the transition guard, just skips booking creation.
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"status": "dipesan"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(Booking.objects.filter(unit=self.unit).exists())

        # Advancing further must not crash just because there's no booking
        resp = self.client.put(
            f"/api/units/{self.unit.id}/", {"status": "proses"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_advancing_does_not_touch_an_already_converted_booking(self):
        """Idempotency: if somehow called twice, don't error or double-log."""
        self._login_as(self.dev)
        self.client.post(
            f"/api/units/{self.unit.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000},
            format="json",
        )
        self.client.put(f"/api/units/{self.unit.id}/", {"status": "proses"}, format="json")

        booking = Booking.objects.get(unit=self.unit)
        self.assertEqual(booking.status, Booking.BookingStatus.CONVERTED)
        # Unit is now "proses" — advancing again isn't a valid
        # transition anyway (proses -> proses is a no-op per the
        # guard), confirming nothing weird happens on a repeat call.
        resp = self.client.put(f"/api/units/{self.unit.id}/", {"status": "proses"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.BookingStatus.CONVERTED)


# =============================================================================
# Sprint 24 — Buyer CRM Basics + KPR Status
# =============================================================================
class BookingKPRStatusTests(APITestCase):
    """
    Sprint 24: KPR status lives on Booking (this sale's financing
    state), not on a separate Buyer profile — deliberately trimmed,
    no transition guard (a rejected KPR reverting to "belum_diajukan"
    to reapply is a normal real-world case, unlike Unit's lifecycle
    which genuinely has illegal jumps worth preventing).
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa KPR Status")
        self.dev = CustomUser.objects.create_user(
            email="dev.kprstatus@test.id", password="pass12345!",
            full_name="Dev KPR Status", role="developer",
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.kprstatus@test.id", password="pass12345!",
            full_name="Buyer KPR Status", role="buyer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster KPR Status", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def _book_unit(self):
        self._login_as(self.dev)
        self.client.post(
            f"/api/units/{self.unit.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000},
            format="json",
        )
        return Booking.objects.get(unit=self.unit)

    def test_new_booking_defaults_to_belum_diajukan(self):
        booking = self._book_unit()
        self.assertEqual(booking.kpr_status, Booking.KPRStatus.BELUM_DIAJUKAN)

    def test_update_kpr_status_succeeds(self):
        booking = self._book_unit()
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/bookings/{booking.id}/kpr/",
            {"kpr_status": "diajukan"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.kpr_status, Booking.KPRStatus.DIAJUKAN)

    def test_kpr_status_can_move_through_full_sequence(self):
        booking = self._book_unit()
        self._login_as(self.dev)
        for new_status in ["diajukan", "disetujui", "akad"]:
            resp = self.client.put(
                f"/api/units/bookings/{booking.id}/kpr/",
                {"kpr_status": new_status}, format="json",
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.kpr_status, Booking.KPRStatus.AKAD)

    def test_kpr_status_can_revert_for_reapplication(self):
        """No transition guard, by design — a rejected/reset KPR
        reverting to belum_diajukan is a normal real-world case."""
        booking = self._book_unit()
        self._login_as(self.dev)
        self.client.put(f"/api/units/bookings/{booking.id}/kpr/", {"kpr_status": "diajukan"}, format="json")
        resp = self.client.put(
            f"/api/units/bookings/{booking.id}/kpr/",
            {"kpr_status": "belum_diajukan"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_invalid_kpr_status_rejected(self):
        booking = self._book_unit()
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/units/bookings/{booking.id}/kpr/",
            {"kpr_status": "not_a_real_status"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_kpr_status_exposed_on_unit_detail(self):
        booking = self._book_unit()
        self._login_as(self.dev)
        self.client.put(f"/api/units/bookings/{booking.id}/kpr/", {"kpr_status": "diajukan"}, format="json")
        resp = self.client.get(f"/api/units/{self.unit.id}/")
        self.assertEqual(resp.data["unit"]["booking"]["kpr_status"], "diajukan")


class BookingStalledTests(APITestCase):
    """
    Sprint 24: is_stalled — a lightweight signal, computed fresh on
    every access, deliberately NOT wired into the Decision Engine
    (that's a heavier system, out of scope for this sprint).
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Stalled")
        self.dev = CustomUser.objects.create_user(
            email="dev.stalled@test.id", password="pass12345!",
            full_name="Dev Stalled", role="developer",
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.stalled@test.id", password="pass12345!",
            full_name="Buyer Stalled", role="buyer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Stalled", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def _book_unit(self, booking_date=None):
        self._login_as(self.dev)
        payload = {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000}
        if booking_date:
            payload["booking_date"] = str(booking_date)
        self.client.post(f"/api/units/{self.unit.id}/book/", payload, format="json")
        return Booking.objects.get(unit=self.unit)

    def test_freshly_booked_is_not_stalled(self):
        booking = self._book_unit()
        self.assertFalse(booking.is_stalled)

    def test_old_booking_with_no_kpr_progress_is_stalled(self):
        old_date = date.today() - timedelta(days=Booking.STALL_THRESHOLD_DAYS + 1)
        booking = self._book_unit(booking_date=old_date)
        self.assertTrue(booking.is_stalled)

    def test_disetujui_is_never_stalled_regardless_of_age(self):
        old_date = date.today() - timedelta(days=30)
        booking = self._book_unit(booking_date=old_date)
        booking.kpr_status = Booking.KPRStatus.DISETUJUI
        booking.save(update_fields=["kpr_status"])
        self.assertFalse(booking.is_stalled)

    def test_akad_is_never_stalled_regardless_of_age(self):
        old_date = date.today() - timedelta(days=30)
        booking = self._book_unit(booking_date=old_date)
        booking.kpr_status = Booking.KPRStatus.AKAD
        booking.save(update_fields=["kpr_status"])
        self.assertFalse(booking.is_stalled)

    def test_cancelled_booking_is_never_stalled(self):
        old_date = date.today() - timedelta(days=30)
        booking = self._book_unit(booking_date=old_date)
        booking.status = Booking.BookingStatus.CANCELLED
        booking.save(update_fields=["status"])
        self.assertFalse(booking.is_stalled)


class BookingTenantIsolationTests(APITestCase):
    """
    Sprint 24: proves the BookingCancelView refactor (hand-rolled
    inline query → Booking.objects.for_user()) didn't quietly change
    behavior — cross-org cancel and the new cross-org KPR update must
    both still be correctly blocked, and the legitimate same-org path
    must still work.
    """

    def setUp(self):
        self.org_a = Organization.objects.create(name="Asri Sentosa Booking Isolation A")
        self.org_b = Organization.objects.create(name="Org B Booking Isolation")

        self.dev_a = CustomUser.objects.create_user(
            email="dev.bookingisolation.a@test.id", password="pass12345!",
            full_name="Dev Booking Isolation A", role="developer",
        )
        self.dev_b = CustomUser.objects.create_user(
            email="dev.bookingisolation.b@test.id", password="pass12345!",
            full_name="Dev Booking Isolation B", role="developer",
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.bookingisolation@test.id", password="pass12345!",
            full_name="Buyer Booking Isolation", role="buyer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

        self.project_a = Project.objects.create(
            organization=self.org_a, name="Cluster Booking Isolation A", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit_a = Unit.objects.create(
            project=self.project_a, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )

        self.client.force_authenticate(user=self.dev_a)
        self.client.post(
            f"/api/units/{self.unit_a.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000},
            format="json",
        )
        self.booking_a = Booking.objects.get(unit=self.unit_a)

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_org_b_cannot_cancel_org_a_booking(self):
        self._login_as(self.dev_b)
        resp = self.client.post(
            f"/api/units/bookings/{self.booking_a.id}/cancel/",
            {"reason": "test"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.booking_a.refresh_from_db()
        self.assertEqual(self.booking_a.status, Booking.BookingStatus.ACTIVE)

    def test_org_b_cannot_update_org_a_booking_kpr_status(self):
        self._login_as(self.dev_b)
        resp = self.client.put(
            f"/api/units/bookings/{self.booking_a.id}/kpr/",
            {"kpr_status": "diajukan"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.booking_a.refresh_from_db()
        self.assertEqual(self.booking_a.kpr_status, Booking.KPRStatus.BELUM_DIAJUKAN)

    def test_org_a_can_still_cancel_its_own_booking(self):
        """Sanity check: the refactor didn't break the legitimate path."""
        self._login_as(self.dev_a)
        resp = self.client.post(
            f"/api/units/bookings/{self.booking_a.id}/cancel/",
            {"reason": "test"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_org_a_can_still_update_its_own_booking_kpr_status(self):
        self._login_as(self.dev_a)
        resp = self.client.put(
            f"/api/units/bookings/{self.booking_a.id}/kpr/",
            {"kpr_status": "diajukan"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class BookingProspectConversionTests(APITestCase):
    """
    Sprint 2 (CRM Foundation): proves the prospect_id wiring added to
    BookingCreateSerializer / UnitBookingView.post(). Four things,
    matching the CRM roadmap's own list — end-to-end conversion, cross-
    org rejection, an invalid id, and — the one that matters most —
    that the pre-existing booking flow is byte-for-byte unchanged when
    prospect_id is simply omitted, exactly as every caller before this
    sprint always did.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Prospect Conversion")
        self.dev = CustomUser.objects.create_user(
            email="dev.prospectconv@test.id", password="pass12345!",
            full_name="Dev Prospect Conversion", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.prospectconv@test.id", password="pass12345!",
            full_name="Buyer Prospect Conversion", role="buyer",
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Prospect Conversion", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )
        self.prospect = Prospect.objects.create(
            organization=self.org, name="Andi Calon Pembeli", phone="081234567890",
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def _book_unit(self, **extra):
        payload = {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000, **extra}
        self._login_as(self.dev)
        return self.client.post(f"/api/units/{self.unit.id}/book/", payload, format="json")

    def test_booking_with_prospect_id_marks_prospect_converted(self):
        resp = self._book_unit(prospect_id=str(self.prospect.id))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.prospect.refresh_from_db()
        # Sprint 5 (CRM Foundation Phase B): KONVERSI renamed WON.
        self.assertEqual(self.prospect.status, Prospect.Status.WON)
        booking = Booking.objects.get(unit=self.unit)
        self.assertEqual(self.prospect.converted_booking_id, booking.id)

    def test_existing_booking_flow_unchanged_without_prospect_id(self):
        """
        The regression test that matters most: every caller before
        this sprint never sent prospect_id at all. Booking must
        succeed exactly as before, and the untouched prospect must
        stay exactly as it started.
        """
        resp = self._book_unit()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, Unit.Status.BOOKED)
        self.assertEqual(self.unit.buyer_id, self.buyer.id)

        self.prospect.refresh_from_db()
        # Sprint 5 (CRM Foundation Phase B): BARU renamed LEAD, and is
        # still the default — an untouched prospect stays untouched.
        self.assertEqual(self.prospect.status, Prospect.Status.LEAD)
        self.assertIsNone(self.prospect.converted_booking)

    def test_cross_org_prospect_id_rejected_with_zero_side_effects(self):
        other_org = Organization.objects.create(name="Org Lain Prospect Conversion")
        foreign_prospect = Prospect.objects.create(
            organization=other_org, name="Prospect Org Lain", phone="081299998888",
        )

        resp = self._book_unit(prospect_id=str(foreign_prospect.id))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Zero side effects — no Booking created, unit still available,
        # the foreign prospect completely untouched.
        self.assertFalse(Booking.objects.filter(unit=self.unit).exists())
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, Unit.Status.AVAILABLE)
        foreign_prospect.refresh_from_db()
        self.assertEqual(foreign_prospect.status, Prospect.Status.LEAD)

    def test_invalid_prospect_id_returns_400(self):
        resp = self._book_unit(prospect_id="00000000-0000-0000-0000-000000000000")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Booking.objects.filter(unit=self.unit).exists())


class BookingCreatesCustomerProfileTests(APITestCase):
    """
    Sprint 8 (CRM Foundation Phase B): CustomerProfile auto-creation
    on booking. Deliberately tests the WALK-IN case (no prospect_id)
    as the primary scenario, not an edge case — this is the deviation
    from the Phase B roadmap's original wording flagged when the
    hook was written: creation is unconditional on prospect_id, not
    nested inside the prospect-conversion block.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa CustomerProfile Hook")
        self.dev = CustomUser.objects.create_user(
            email="dev.customerprofilehook@test.id", password="pass12345!",
            full_name="Dev CustomerProfile Hook", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.customerprofilehook@test.id", password="pass12345!",
            full_name="Buyer CustomerProfile Hook", role="buyer",
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster CustomerProfile Hook", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit_a = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )
        self.unit_b = Unit.objects.create(
            project=self.project, unit_number="A-02", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )
        self.client.force_authenticate(user=self.dev)

    def test_walk_in_booking_with_no_prospect_id_still_creates_customer_profile(self):
        """The primary case: no CRM history at all, still a real customer."""
        resp = self.client.post(
            f"/api/units/{self.unit_a.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            CustomerProfile.objects.filter(user=self.buyer, organization=self.org).exists()
        )

    def test_second_booking_same_buyer_same_org_does_not_duplicate_profile(self):
        """A buyer booking a second unit in the same org must not
        create a second CustomerProfile row — get_or_create +
        unique_together(user, organization) both guard against this."""
        self.client.post(
            f"/api/units/{self.unit_a.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000},
            format="json",
        )
        self.client.post(
            f"/api/units/{self.unit_b.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000},
            format="json",
        )
        self.assertEqual(
            CustomerProfile.objects.filter(user=self.buyer, organization=self.org).count(), 1
        )

    def test_booking_with_prospect_id_also_creates_customer_profile(self):
        """The CRM-tracked path still works too — this isn't an
        either/or with the prospect conversion wiring."""
        prospect = Prospect.objects.create(organization=self.org, name="Andi", phone="081200000000")
        resp = self.client.post(
            f"/api/units/{self.unit_a.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000, "prospect_id": str(prospect.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            CustomerProfile.objects.filter(user=self.buyer, organization=self.org).exists()
        )


class BookingCreatesCommissionTests(APITestCase):
    """
    Commission Foundation Sprint 1: conditional Commission creation.
    Deliberately tests both the positive case (assigned agent → real
    Commission) and negative cases (no agent, or no Prospect at all →
    no Commission) as equally important, not edge cases — the whole
    design point of this hook is that it's conditional, unlike
    CustomerProfile's unconditional one.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Commission Hook")
        self.dev = CustomUser.objects.create_user(
            email="dev.commissionhook@test.id", password="pass12345!",
            full_name="Dev Commission Hook", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.agent = CustomUser.objects.create_user(
            email="agent.commissionhook@test.id", password="pass12345!",
            full_name="Agent Commission Hook", role="agent",
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.commissionhook@test.id", password="pass12345!",
            full_name="Buyer Commission Hook", role="buyer",
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Commission Hook", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.unit_a = Unit.objects.create(
            project=self.project, unit_number="A-01", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )
        self.unit_b = Unit.objects.create(
            project=self.project, unit_number="A-02", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )
        self.unit_c = Unit.objects.create(
            project=self.project, unit_number="A-03", unit_type="Tipe 45",
            land_area=90, building_area=45, price=500_000_000,
        )
        CommissionPolicy.objects.create(
            organization=self.org,
            rate_type=CommissionPolicy.RateType.PERCENTAGE,
            rate_value=Decimal("2.5"),
        )
        self.client.force_authenticate(user=self.dev)

    def test_booking_with_prospect_and_assigned_agent_creates_commission(self):
        prospect = Prospect.objects.create(
            organization=self.org, name="Andi", phone="081200000000",
            assigned_to=self.agent,
        )
        resp = self.client.post(
            f"/api/units/{self.unit_a.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000, "prospect_id": str(prospect.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(unit=self.unit_a)
        commission = Commission.objects.get(booking=booking)
        self.assertEqual(commission.agent_id, self.agent.id)
        self.assertEqual(commission.amount, Decimal("12500000"))
        self.assertEqual(commission.status, Commission.Status.PENDING)

    def test_booking_with_prospect_but_no_assigned_agent_creates_no_commission(self):
        prospect = Prospect.objects.create(
            organization=self.org, name="Budi", phone="081200000001",
            assigned_to=None,
        )
        resp = self.client.post(
            f"/api/units/{self.unit_b.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000, "prospect_id": str(prospect.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(unit=self.unit_b)
        self.assertFalse(Commission.objects.filter(booking=booking).exists())

    def test_walk_in_booking_with_no_prospect_creates_no_commission(self):
        """The primary contrast with Sprint 8's CustomerProfile hook:
        CustomerProfile is unconditional here, Commission is not."""
        resp = self.client.post(
            f"/api/units/{self.unit_c.id}/book/",
            {"buyer_id": str(self.buyer.id), "booking_fee": 10_000_000},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(unit=self.unit_c)
        self.assertFalse(Commission.objects.filter(booking=booking).exists())
        # But CustomerProfile still got created — proving the two
        # hooks really are independent, not accidentally coupled.
        self.assertTrue(
            CustomerProfile.objects.filter(user=self.buyer, organization=self.org).exists()
        )
