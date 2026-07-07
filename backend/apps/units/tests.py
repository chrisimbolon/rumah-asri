from datetime import date, timedelta

from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser
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
