# =============================================================================
# === backend/apps/payments/management/commands/mark_overdue_payments.py ===
# =============================================================================
"""
Sprint 25: sweeps "menunggu" (pending) payments whose due_date has
passed and flips them to "menunggak" (overdue).

Payment.is_overdue already computes this live on every access, so
nothing in this codebase was actually broken without this command —
but leaving genuinely-overdue payments sitting in "menunggu" forever
means any code that filters directly on status="menunggak" (a report,
an export, a future integration) would silently miss them unless it
also remembers the exact OR-condition every time. This command makes
the stored status tell the truth too, not just the live property.

Deliberately does NOT touch "akan_datang" (upcoming) payments, even
past their due_date — matches Payment.is_overdue's existing exclusion,
not a new interpretation.

Meant to run daily via cron, same pattern as expire_bookings:

    0 3 * * * docker exec developindo_backend python manage.py mark_overdue_payments >> /var/log/mark_overdue_payments.log 2>&1
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.payments.models import FinancialAudit, Payment


class Command(BaseCommand):
    help = "Flips pending payments past their due date to 'menunggak' (overdue)."

    def handle(self, *args, **options):
        # Sprint 25 bugfix: timezone.now().date() returns the UTC
        # calendar date, which silently disagrees with the real
        # Asia/Jakarta date for several hours around local midnight.
        # timezone.localdate() gives the correct local date.
        today = timezone.localdate()

        overdue_qs = Payment.objects.filter(
            status=Payment.Status.PENDING,
            due_date__lt=today,
        ).select_related("unit")

        count = 0
        for payment in overdue_qs:
            ar_before = payment.unit.ar_outstanding

            payment.status = Payment.Status.OVERDUE
            payment.save(update_fields=["status", "updated_at"])

            # Sprint 27: changed_by deliberately omitted (defaults to
            # None) — this is a system sweep, not a human decision.
            # Pretending a user "approved" this would be dishonest.
            # AR itself doesn't move here (status="menunggak" still
            # isn't "lunas"), but logging ar_before == ar_after is more
            # honest than leaving both fields null and implying we
            # didn't check.
            FinancialAudit.log(
                organization = payment.organization,
                action       = FinancialAudit.Action.PAYMENT_MARKED_OVERDUE,
                payment      = payment,
                unit         = payment.unit,
                old_value    = Payment.Status.PENDING,
                new_value    = Payment.Status.OVERDUE,
                notes        = f"Jatuh tempo {payment.due_date}, disapu otomatis",
                ar_before    = ar_before,
                ar_after     = payment.unit.ar_outstanding,
            )

            self.stdout.write(
                f"  ✓ Unit {payment.unit.unit_number} — {payment.payment_type} "
                f"kini menunggak (jatuh tempo {payment.due_date})"
            )
            count += 1

        self.stdout.write(f"Done. Payments marked overdue: {count}")
