# =============================================================================
# === backend/apps/crm/tests.py ===
# CRM Foundation Sprint 1: Prospect model tests.
#
# Plain TestCase, not APITestCase — this sprint ships the model only,
# no views/serializers/urls yet (those land in Sprint 2/3). Everything
# here exercises the model and its TenantScopedModel contract directly,
# same rigor as every other model this engagement, no exceptions for
# being "just a foundation."
# =============================================================================
from datetime import date, timedelta

from django.test import TestCase

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership
from apps.projects.models import Project

from .models import Prospect


class ProspectTestBase(TestCase):
    """Shared scaffolding: one org, one project, one developer."""

    def setUp(self):
        self.org = Organization.objects.create(name="PT Asri Sentosa Properti")
        self.dev = CustomUser.objects.create_user(
            email="dev@asrisentosa.id", password="pass12345!",
            full_name="Budi Developer", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Perumahan Asri Cluster A", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )


class ProspectCreationTests(ProspectTestBase):

    def test_create_prospect_with_minimal_fields(self):
        """name + phone + explicit organization is enough — everything
        else (interested_project, assigned_to, notes, followup date)
        is genuinely optional, matching the roadmap's 'minimal' model."""
        prospect = Prospect.objects.create(
            organization=self.org, name="Andi Calon Pembeli", phone="081234567890",
        )
        self.assertEqual(prospect.status, Prospect.Status.BARU)
        self.assertIsNone(prospect.interested_project)
        self.assertIsNone(prospect.assigned_to)
        self.assertIsNone(prospect.converted_booking)
        self.assertEqual(prospect.source, "")
        self.assertIsNotNone(prospect.created_at)

    def test_create_prospect_with_all_fields(self):
        prospect = Prospect.objects.create(
            organization=self.org,
            name="Citra Calon Pembeli",
            phone="081298765432",
            source="Referral",
            interested_project=self.project,
            assigned_to=self.dev,
            status=Prospect.Status.FOLLOW_UP,
            next_followup_date=date.today() + timedelta(days=3),
            notes="Tertarik unit 45/90, minta simulasi KPR.",
        )
        self.assertEqual(prospect.interested_project, self.project)
        self.assertEqual(prospect.assigned_to, self.dev)
        self.assertEqual(prospect.status, Prospect.Status.FOLLOW_UP)

    def test_str_representation(self):
        prospect = Prospect.objects.create(
            organization=self.org, name="Dedi Calon Pembeli", phone="081200000000",
        )
        self.assertIn("Dedi Calon Pembeli", str(prospect))
        self.assertIn("Baru", str(prospect))


class ProspectOrganizationResolutionTests(ProspectTestBase):
    """
    TenantScopedModel's _resolve_organization() contract: derive from
    the parent relation when present, otherwise the caller must set
    `organization` explicitly — same requirement Project itself has.
    """

    def test_organization_resolved_from_interested_project_when_not_explicit(self):
        prospect = Prospect.objects.create(
            name="Eka Calon Pembeli", phone="081211112222",
            interested_project=self.project,
        )
        self.assertEqual(prospect.organization_id, self.org.id)

    def test_explicit_organization_is_not_overridden_by_resolution(self):
        other_org = Organization.objects.create(name="Org Lain")
        prospect = Prospect.objects.create(
            organization=other_org, name="Fajar Calon Pembeli", phone="081233334444",
            interested_project=self.project,
        )
        # Explicit organization wins — save() only resolves when
        # organization_id is None going in.
        self.assertEqual(prospect.organization_id, other_org.id)

    def test_organization_stays_null_with_no_project_and_no_explicit_org(self):
        """
        Documents current behavior rather than asserting it's ideal:
        TenantScopedModel allows a null organization by design (see
        core/models.py docstring). A prospect created with neither an
        explicit org nor a project is technically valid at the model
        layer — it's the future ProspectCreateSerializer's job to
        reject this, the same division of responsibility Project has.
        """
        prospect = Prospect.objects.create(name="Gita Calon Pembeli", phone="081255556666")
        self.assertIsNone(prospect.organization_id)


class ProspectTenantIsolationTests(TestCase):
    """
    Proves Prospect.objects.for_user() — inherited for free from
    TenantScopedModel/TenantScopedManager — correctly separates orgs
    with zero custom code written for it. This is the whole point of
    building on TenantScopedModel instead of duplicating Booking's
    manual BookingQuerySet.for_user() pattern.
    """

    def setUp(self):
        self.org_a = Organization.objects.create(name="Asri Sentosa CRM Isolation A")
        self.org_b = Organization.objects.create(name="Org B CRM Isolation")

        self.dev_a = CustomUser.objects.create_user(
            email="dev.crmisolation.a@test.id", password="pass12345!",
            full_name="Dev CRM Isolation A", role="developer",
        )
        self.dev_b = CustomUser.objects.create_user(
            email="dev.crmisolation.b@test.id", password="pass12345!",
            full_name="Dev CRM Isolation B", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

        self.prospect_a = Prospect.objects.create(
            organization=self.org_a, name="Prospect Org A", phone="081200000001",
        )
        self.prospect_b = Prospect.objects.create(
            organization=self.org_b, name="Prospect Org B", phone="081200000002",
        )

    def test_dev_a_sees_only_org_a_prospects(self):
        visible = Prospect.objects.for_user(self.dev_a)
        self.assertIn(self.prospect_a, visible)
        self.assertNotIn(self.prospect_b, visible)

    def test_dev_b_sees_only_org_b_prospects(self):
        visible = Prospect.objects.for_user(self.dev_b)
        self.assertIn(self.prospect_b, visible)
        self.assertNotIn(self.prospect_a, visible)

    def test_super_admin_sees_all_prospects(self):
        admin = CustomUser.objects.create_user(
            email="admin.crmisolation@developindo.id", password="pass12345!",
            full_name="Platform Admin", role="super_admin",
        )
        visible = Prospect.objects.for_user(admin)
        self.assertIn(self.prospect_a, visible)
        self.assertIn(self.prospect_b, visible)

    def test_user_with_no_membership_sees_no_prospects(self):
        outsider = CustomUser.objects.create_user(
            email="outsider.crmisolation@test.id", password="pass12345!",
            full_name="No Org User", role="developer",
        )
        visible = Prospect.objects.for_user(outsider)
        self.assertEqual(visible.count(), 0)


class ProspectConvertedBookingFieldTests(ProspectTestBase):
    """
    Sprint 1 only proves the field exists and behaves as a plain
    nullable OneToOne — the actual conversion *logic* (setting status
    to konversi, wiring it from UnitBookingView.post()) is Sprint 2's
    job, deliberately not tested here.
    """

    def test_converted_booking_defaults_to_none(self):
        prospect = Prospect.objects.create(
            organization=self.org, name="Hadi Calon Pembeli", phone="081277778888",
        )
        self.assertIsNone(prospect.converted_booking)

    def test_converted_booking_accepts_null_on_creation(self):
        """Regression guard: Sprint 2 must be able to create a Prospect
        and set converted_booking later without this field getting in
        the way — it should never be required at creation time."""
        prospect = Prospect(
            organization=self.org, name="Indah Calon Pembeli", phone="081200001111",
        )
        prospect.full_clean(exclude=["converted_booking"])
        prospect.save()
        self.assertIsNone(prospect.converted_booking)
