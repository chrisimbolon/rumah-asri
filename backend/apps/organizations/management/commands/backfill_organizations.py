# =============================================================================
# === apps/organizations/management/commands/backfill_organizations.py ===
# =============================================================================
"""
One-time backfill: create an Organization + OrganizationMembership for
every existing CustomUser with role=developer, then point their existing
Projects (and transitively Units/Payments/Documents/ConstructionPhases)
at that Organization.

SEQUENCING — this only works if run in this exact order:
  1. apps.organizations is migrated (Organization/OrganizationMembership
     tables exist).
  2. apps.projects/units/payments/documents/construction have had
     `organization` added as a NULLABLE field via makemigrations+migrate,
     and Project STILL has its old `developer` field (do not delete it
     before running this command — see STAGE 2 note in projects/models.py).
  3. THEN run: python manage.py backfill_organizations

Usage:
  python manage.py backfill_organizations
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership
from apps.projects.models import Project


class Command(BaseCommand):
    help = "Backfill Organization + OrganizationMembership for existing developers"

    @transaction.atomic
    def handle(self, *args, **options):
        developers = CustomUser.objects.filter(role="developer")
        self.stdout.write(f"Found {developers.count()} developer account(s)")

        for dev in developers:
            org, org_created = Organization.objects.get_or_create(
                name=f"{dev.full_name} Properti",
            )
            OrganizationMembership.objects.get_or_create(
                organization=org, user=dev, defaults={"role": "owner"},
            )
            updated = Project.objects.filter(
                developer=dev, organization__isnull=True
            ).update(organization=org)
            self.stdout.write(
                f"  {dev.email} -> {org.name} "
                f"({'created' if org_created else 'existing'}, {updated} project(s) linked)"
            )

        # ── Denormalize organization onto everything that hangs off Unit ──
        from apps.construction.models import ConstructionPhase
        from apps.documents.models import Document
        from apps.payments.models import Payment
        from apps.units.models import Unit

        for unit in Unit.objects.filter(organization__isnull=True).select_related("project"):
            unit.organization = unit.project.organization
            unit.save(update_fields=["organization"])

        for payment in Payment.objects.filter(organization__isnull=True).select_related("unit"):
            payment.organization = payment.unit.organization
            payment.save(update_fields=["organization"])

        for doc in Document.objects.filter(organization__isnull=True).select_related("unit"):
            doc.organization = doc.unit.organization
            doc.save(update_fields=["organization"])

        for phase in ConstructionPhase.objects.filter(organization__isnull=True).select_related("unit"):
            phase.organization = phase.unit.organization
            phase.save(update_fields=["organization"])

        remaining = Project.objects.filter(organization__isnull=True).count()
        if remaining:
            self.stdout.write(self.style.WARNING(
                f"⚠️  {remaining} project(s) still have no organization — "
                "check for non-developer-owned projects before proceeding."
            ))
        self.stdout.write(self.style.SUCCESS("✅ Backfill complete"))
