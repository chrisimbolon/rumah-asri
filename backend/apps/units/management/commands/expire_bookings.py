# =============================================================================
# === backend/apps/units/management/commands/expire_bookings.py ===
# =============================================================================
"""
Sprint 23: auto-expire ACTIVE bookings past their expires_at deadline.

Without this, a "dipesan" unit could sit reserved forever with zero
pressure to actually pay the booking fee — this is the piece that gives
the "sell first, build second" model real teeth. Meant to run daily via
cron, same pattern as snapshot_portfolio_daily / snapshot_risk_daily:

    0 2 * * * docker exec developindo_backend python manage.py expire_bookings >> /var/log/expire_bookings.log 2>&1
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.units.models import Booking, Unit


class Command(BaseCommand):
    help = "Expires ACTIVE bookings past their deadline, reverting the unit back to tersedia."

    def handle(self, *args, **options):
        now = timezone.now()

        expired_qs = Booking.objects.filter(
            status=Booking.BookingStatus.ACTIVE,
            expires_at__isnull=False,
            expires_at__lt=now,
        ).select_related("unit")

        count = 0
        for booking in expired_qs:
            unit = booking.unit

            booking.status = Booking.BookingStatus.EXPIRED
            booking.save(update_fields=["status", "updated_at"])

            unit.status = Unit.Status.AVAILABLE
            unit.buyer  = None
            unit.save(update_fields=["status", "buyer", "updated_at"])

            self.stdout.write(
                f"  ✓ {booking.spr_number} kedaluwarsa — "
                f"unit {unit.unit_number} kembali tersedia"
            )
            count += 1

        self.stdout.write(f"Done. Bookings expired: {count}")
