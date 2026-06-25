# =============================================================================
# === apps/core/models.py ===
# =============================================================================
"""
Shared abstract base for every model that belongs to exactly one
Organization (the SaaS tenant). The whole point of this file: make it
structurally awkward to write a query that skips tenant filtering,
rather than relying on every view remembering to add it by hand —
which is exactly what went wrong with PaymentDetailView (no filter at
all) and UnitDetailView (filter present for some roles, silently
absent for others, e.g. agent).
"""
import uuid

from django.db import models

from apps.organizations.models import Organization


class TenantScopedQuerySet(models.QuerySet):
    def for_user(self, user):
        """
        The one supported entry point for fetching tenant-scoped rows.
        super_admin (DevelopIndo platform staff) sees everything.
        Everyone else sees only rows in an organization they have an
        active membership in.
        """
        if getattr(user, "role", None) == "super_admin":
            return self
        org_ids = user.memberships.filter(is_active=True).values_list(
            "organization_id", flat=True
        )
        return self.filter(organization_id__in=org_ids)


class TenantScopedManager(models.Manager):
    def get_queryset(self):
        return TenantScopedQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)


class TenantScopedModel(models.Model):
    """
    Abstract base. Subclasses get an `organization` FK and the
    `.objects.for_user(user)` manager method for free.

    `organization` is nullable for now — intentional. It lets us add this
    field to tables that already have rows, backfill them with the
    management command, and only tighten to null=False in a follow-up
    migration once zero NULL rows remain. That's the standard safe
    sequence for adding a required relationship to a populated table.

    Subclasses that derive their organization from a parent relation
    (e.g. Unit derives it from `project`) should override
    `_resolve_organization()`. Subclasses with no natural parent (e.g.
    Project itself) must have `organization` set explicitly before save
    — see ProjectCreateSerializer.create().
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="+",
        null=True, blank=True,
    )

    objects = TenantScopedManager()

    class Meta:
        abstract = True

    def _resolve_organization(self):
        return None

    def save(self, *args, **kwargs):
        if self.organization_id is None:
            resolved = self._resolve_organization()
            if resolved is not None:
                self.organization = resolved
        super().save(*args, **kwargs)
