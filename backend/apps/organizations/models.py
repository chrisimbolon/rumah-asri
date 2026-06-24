# =============================================================================
# === apps/organizations/models.py ===
# =============================================================================
"""
DevelopIndo — Organization (tenant) model.

This is the actual SaaS tenant — a developer COMPANY, not an individual
CustomUser account. Project/Unit/Payment/Document/ConstructionPhase all
belong to an Organization, not directly to a user. This is what makes a
developer company able to have a second admin, a project manager, or a
sales agent under one account — which the old `Project.developer ->
CustomUser` FK could never support.
"""
import uuid

from django.conf import settings
from django.db import models


class Organization(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField(max_length=200, verbose_name="Nama Perusahaan")
    plan       = models.CharField(max_length=20, default="trial", verbose_name="Paket")
    is_active  = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Organisasi"
        verbose_name_plural = "Organisasi"
        ordering            = ["name"]

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    """
    Join table: which users belong to which organization, and in what
    capacity. This replaces CustomUser.developer (the old self-FK)
    entirely — a user's tenant is determined by their membership row,
    not by a field on CustomUser pointing at another CustomUser.
    """

    class MembershipRole(models.TextChoices):
        OWNER = "owner", "Pemilik"
        ADMIN = "admin", "Admin"
        AGENT = "agent", "Agen Penjualan"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships",
    )
    role       = models.CharField(
        max_length=20, choices=MembershipRole.choices, default=MembershipRole.AGENT,
    )
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Keanggotaan Organisasi"
        verbose_name_plural = "Keanggotaan Organisasi"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="uq_org_membership_user",
            )
        ]

    def __str__(self):
        return f"{self.user.full_name} @ {self.organization.name} ({self.role})"
