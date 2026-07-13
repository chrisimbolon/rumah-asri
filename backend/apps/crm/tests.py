# =============================================================================
# === backend/apps/crm/tests.py ===
# CRM Foundation Sprint 1: Prospect model tests (plain TestCase — no
# views/serializers/urls existed yet).
#
# Sprint 2.5 adds ProspectAPITests below, covering the CRUD endpoints
# that now exist. The Sprint 1 classes above stay as plain TestCase on
# purpose — they test the model/TenantScopedModel contract directly
# and don't need HTTP round-tripping to do that.
# =============================================================================
from datetime import date, timedelta

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

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


class ProspectAPITestBase(APITestCase):
    """Shared scaffolding for the Sprint 2.5 CRUD endpoint tests:
    one org, one project, a developer, an agent, and a buyer (to
    prove the role gate actually excludes someone)."""

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa CRM API")
        self.dev = CustomUser.objects.create_user(
            email="dev.crmapi@test.id", password="pass12345!",
            full_name="Dev CRM API", role="developer",
        )
        self.agent = CustomUser.objects.create_user(
            email="agent.crmapi@test.id", password="pass12345!",
            full_name="Agent CRM API", role="agent",
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.crmapi@test.id", password="pass12345!",
            full_name="Buyer CRM API", role="buyer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.agent, role="member", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster CRM API", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)


class ProspectCreateTests(ProspectAPITestBase):

    def test_developer_can_create_prospect_without_project(self):
        self._login_as(self.dev)
        resp = self.client.post(
            "/api/prospects/",
            {"name": "Andi Calon Pembeli", "phone": "081234567890"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        prospect = Prospect.objects.get(id=resp.data["prospect"]["id"])
        # Organization resolved explicitly by the serializer, not the
        # model, since there's no interested_project to derive it from.
        self.assertEqual(prospect.organization_id, self.org.id)

    def test_agent_can_create_prospect(self):
        self._login_as(self.agent)
        resp = self.client.post(
            "/api/prospects/",
            {"name": "Budi Calon Pembeli", "phone": "081211112222"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_buyer_cannot_create_prospect(self):
        self._login_as(self.buyer)
        resp = self.client.post(
            "/api/prospects/",
            {"name": "Citra Calon Pembeli", "phone": "081233334444"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_with_interested_project_resolves_org_from_project(self):
        self._login_as(self.dev)
        resp = self.client.post(
            "/api/prospects/",
            {
                "name": "Dedi Calon Pembeli", "phone": "081255556666",
                "interested_project": str(self.project.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        prospect = Prospect.objects.get(id=resp.data["prospect"]["id"])
        self.assertEqual(prospect.organization_id, self.org.id)

    def test_cannot_attach_prospect_to_project_outside_own_org(self):
        other_org = Organization.objects.create(name="Org Lain CRM API")
        foreign_project = Project.objects.create(
            organization=other_org, name="Cluster Org Lain", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self._login_as(self.dev)
        resp = self.client.post(
            "/api/prospects/",
            {
                "name": "Eka Calon Pembeli", "phone": "081277778888",
                "interested_project": str(foreign_project.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buyer_cannot_be_assigned_to_a_prospect(self):
        self._login_as(self.dev)
        resp = self.client.post(
            "/api/prospects/",
            {
                "name": "Fajar Calon Pembeli", "phone": "081200001111",
                "assigned_to": str(self.buyer.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agent_can_be_assigned_to_a_prospect(self):
        self._login_as(self.dev)
        resp = self.client.post(
            "/api/prospects/",
            {
                "name": "Gita Calon Pembeli", "phone": "081222223333",
                "assigned_to": str(self.agent.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


class ProspectListDetailUpdateTests(ProspectAPITestBase):

    def setUp(self):
        super().setUp()
        self.prospect = Prospect.objects.create(
            organization=self.org, name="Hadi Calon Pembeli", phone="081200002222",
        )

    def test_list_returns_org_prospects(self):
        self._login_as(self.dev)
        resp = self.client.get("/api/prospects/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_list_filters_by_status(self):
        Prospect.objects.create(
            organization=self.org, name="Indah Calon Pembeli", phone="081200003333",
            status=Prospect.Status.HILANG,
        )
        self._login_as(self.dev)
        resp = self.client.get("/api/prospects/?status=hilang")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["name"], "Indah Calon Pembeli")

    def test_detail_returns_prospect(self):
        self._login_as(self.dev)
        resp = self.client.get(f"/api/prospects/{self.prospect.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["prospect"]["name"], "Hadi Calon Pembeli")

    def test_developer_can_update_status_and_followup_date(self):
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/prospects/{self.prospect.id}/",
            {"status": "follow_up", "next_followup_date": str(date.today() + timedelta(days=2))},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.prospect.refresh_from_db()
        self.assertEqual(self.prospect.status, Prospect.Status.FOLLOW_UP)

    def test_buyer_cannot_update_prospect(self):
        self._login_as(self.buyer)
        resp = self.client.put(
            f"/api/prospects/{self.prospect.id}/",
            {"status": "follow_up"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_cannot_set_converted_booking_directly(self):
        """converted_booking is intentionally excluded from
        ProspectCreateSerializer's fields — a client can't fake a
        conversion through this endpoint, only UnitBookingView.post()
        can set this field."""
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/prospects/{self.prospect.id}/",
            {"converted_booking": "00000000-0000-0000-0000-000000000000"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.prospect.refresh_from_db()
        self.assertIsNone(self.prospect.converted_booking)


class ProspectAPITenantIsolationTests(ProspectAPITestBase):

    def setUp(self):
        super().setUp()
        self.other_org = Organization.objects.create(name="Org Lain CRM API Isolation")
        self.other_dev = CustomUser.objects.create_user(
            email="dev.crmapiisolation.other@test.id", password="pass12345!",
            full_name="Dev Org Lain", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.other_org, user=self.other_dev, role="owner", is_active=True,
        )
        self.prospect = Prospect.objects.create(
            organization=self.org, name="Joko Calon Pembeli", phone="081200004444",
        )

    def test_org_b_cannot_see_org_a_prospect_in_list(self):
        self._login_as(self.other_dev)
        resp = self.client.get("/api/prospects/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_org_b_cannot_retrieve_org_a_prospect_detail(self):
        self._login_as(self.other_dev)
        resp = self.client.get(f"/api/prospects/{self.prospect.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_org_b_cannot_update_org_a_prospect(self):
        self._login_as(self.other_dev)
        resp = self.client.put(
            f"/api/prospects/{self.prospect.id}/",
            {"status": "hilang"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.prospect.refresh_from_db()
        self.assertEqual(self.prospect.status, Prospect.Status.BARU)
