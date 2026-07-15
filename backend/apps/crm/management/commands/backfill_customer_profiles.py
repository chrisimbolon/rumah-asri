# =============================================================================
# === backend/apps/crm/management/commands/backfill_customer_profiles.py ===
# Sprint 8 (CRM Foundation Phase B).
#
# CustomerProfile is auto-created going forward by
# UnitBookingView.post() — but any Booking that existed BEFORE this
# migration shipped has a real buyer with no CustomerProfile yet.
# Same "additive migration, then backfill" sequence already
# established by apps/organizations/management/commands/
# backfill_organizations.py — nothing new invented here, just applied
# to this model.
#
# Safe to run multiple times: get_or_create + unique_together(user,
# organization) means re-running this never creates duplicates.
# =============================================================================
from django.core.management.base import BaseCommand

from apps.crm.models import CustomerProfile
from apps.units.models import Booking


class Command(BaseCommand):
    help = "Backfill CustomerProfile for every buyer with an existing Booking."

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        # Every Booking that ever existed has a real buyer and a real
        # organization — both required fields on Booking already, so
        # nothing here is ever guessing at a null value.
        for booking in Booking.objects.select_related("buyer", "organization").all():
            _, created = CustomerProfile.objects.get_or_create(
                user=booking.buyer,
                organization=booking.organization,
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. CustomerProfiles created: {created_count}, "
            f"already existed: {skipped_count}."
        ))
