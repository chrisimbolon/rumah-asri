# =============================================================================
# === backend/apps/projects/management/commands/snapshot_risk_daily.py ===
# Sprint 6: Daily risk snapshot for all active projects
# Run via cron or manually:
#   python manage.py snapshot_risk_daily
#   python manage.py snapshot_risk_daily --org-id <uuid>
# =============================================================================
"""
DevelopIndo — Daily Risk Snapshot

Stores today's risk score for every active project.
Enables 30-day risk trend sparkline in the UI.

Recommended cron (server time = UTC, Jambi = UTC+7):
  0 1 * * * docker exec developindo_backend python manage.py snapshot_risk_daily
  (runs at 01:00 UTC = 08:00 Jambi, before the work day starts)

Usage:
  python manage.py snapshot_risk_daily
  python manage.py snapshot_risk_daily --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.projects.models import Project, RiskSnapshot


class Command(BaseCommand):
    help = "Store daily risk snapshot for all active projects (Sprint 6)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be snapshotted without saving",
        )
        parser.add_argument(
            "--org-id",
            type=str,
            help="Only snapshot projects for a specific organization UUID",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        org_id  = options.get("org_id")

        projects = Project.objects.exclude(
            stage__in=["selesai", "ditunda"]
        ).select_related("organization")

        if org_id:
            projects = projects.filter(organization_id=org_id)

        total     = projects.count()
        snapped   = 0
        errors    = 0
        today     = timezone.now().date()

        self.stdout.write(f"📊 Daily risk snapshot — {today}")
        self.stdout.write(f"   Projects to process: {total}")
        if dry_run:
            self.stdout.write("   [DRY RUN — no data will be saved]")
        self.stdout.write("")

        for p in projects:
            try:
                risk_data = p._get_risk_data()
                score     = risk_data["score"]
                level     = risk_data["level"]
                level_display = {"low": "Rendah", "medium": "Sedang", "high": "Tinggi"}.get(level, level)

                if dry_run:
                    self.stdout.write(
                        f"  [DRY] {p.name}: score={score} ({level_display})"
                    )
                else:
                    p.snapshot_risk()
                    self.stdout.write(
                        f"  ✅ {p.name}: score={score} ({level_display})"
                    )
                snapped += 1

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ {p.name}: {e}")
                )

        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"[DRY RUN] Would have snapped {snapped} projects, {errors} errors"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"🎉 Done! {snapped} projects snapped, {errors} errors"
            ))
            self.stdout.write(f"   Total RiskSnapshots today: {RiskSnapshot.objects.filter(snapped_at=today).count()}")
