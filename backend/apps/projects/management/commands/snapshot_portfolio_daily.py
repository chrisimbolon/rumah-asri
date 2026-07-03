# =============================================================================
# backend/apps/projects/management/commands/snapshot_portfolio_daily.py
# Sprint 18: Daily portfolio snapshot command.
#
# Run manually:   python manage.py snapshot_portfolio_daily
# Run with cron:  0 2 * * * cd /app && python manage.py snapshot_portfolio_daily
# (2am daily — quiet hours, data from previous day is captured)
#
# Creates/updates one PortfolioSnapshot per active organization per day.
# Uses update_or_create — safe to run multiple times on same day.
# =============================================================================
from datetime import date

from django.core.management.base import BaseCommand

from apps.organizations.models import Organization


# NOTE: Import PortfolioSnapshot directly:
# from apps.projects.models import PortfolioSnapshot
# Written this way to make the instruction explicit — see SPRINT18_INSTRUCTIONS.md


class Command(BaseCommand):
    help = "Write daily portfolio intelligence snapshots for all active organizations."

    def handle(self, *args, **options):
        from apps.projects.models import PortfolioSnapshot, Project

        today    = date.today()
        orgs     = Organization.objects.filter(is_active=True)
        created  = 0
        skipped  = 0

        for org in orgs:
            projects = list(Project.objects.filter(organization=org))
            if not projects:
                skipped += 1
                continue

            total           = len(projects)
            avg_readiness   = round(
                sum(p.readiness_score for p in projects) / total, 1
            ) if total else 0.0
            critical_count  = sum(1 for p in projects if p.blocking_count > 0)
            high_risk_count = sum(1 for p in projects if p.risk_level == "high")
            delayed_count   = sum(
                1 for p in projects
                if p.end_date and p.end_date < today
                and p.stage not in ("selesai", "serah_terima")
            )
            revenue_protected = int(sum(
                float(p.target_budget)
                for p in projects
                if p.target_budget
                and p.stage not in ("selesai", "serah_terima")
            ))

            PortfolioSnapshot.objects.update_or_create(
                organization=org,
                snapped_at=today,
                defaults={
                    "total_projects":    total,
                    "avg_readiness":     avg_readiness,
                    "critical_count":    critical_count,
                    "high_risk_count":   high_risk_count,
                    "delayed_count":     delayed_count,
                    "revenue_protected": revenue_protected,
                },
            )
            created += 1
            self.stdout.write(
                f"  ✓ {org.name}: {total} projects, "
                f"avg_readiness={avg_readiness}%, "
                f"critical={critical_count}, "
                f"revenue=Rp {revenue_protected:,}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Snapshots written: {created}, orgs skipped (no projects): {skipped}"
            )
        )
