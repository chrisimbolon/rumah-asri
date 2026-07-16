# =============================================================================
# === backend/apps/organizations/tests_agent_list.py ===
# =============================================================================
"""
AgentListView tests — kept in a dedicated file rather than appended to
tests.py, since that file wasn't available to safely edit. Same
precedent apps/payments/tests_financial_audit.py and
apps/projects/tests_site_plan.py already established in this codebase.
"""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser

from .models import Organization, OrganizationMembership


class AgentListViewTests(APITestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Asri Sentosa Agent List")
        self.dev = CustomUser.objects.create_user(
            email="dev.agentlist@test.id", password="pass12345!",
            full_name="Dev Agent List", role="developer",
        )
        self.agent_a = CustomUser.objects.create_user(
            email="agent.a.agentlist@test.id", password="pass12345!",
            full_name="Agent A", role="agent",
        )
        self.agent_b = CustomUser.objects.create_user(
            email="agent.b.agentlist@test.id", password="pass12345!",
            full_name="Agent B", role="agent",
        )
        self.buyer = CustomUser.objects.create_user(
            email="buyer.agentlist@test.id", password="pass12345!",
            full_name="Buyer Agent List", role="buyer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.agent_a, role="member", is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.agent_b, role="member", is_active=True,
        )
        self.client.force_authenticate(user=self.dev)

    def test_returns_developer_and_agent_roles(self):
        resp = self.client.get("/api/organizations/agents/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = {r["full_name"] for r in resp.data["results"]}
        self.assertIn("Agent A", names)
        self.assertIn("Agent B", names)
        self.assertIn("Dev Agent List", names)

    def test_excludes_buyers(self):
        """The buyer, though a real active user, must never appear —
        Prospect.assigned_to only accepts developer/agent roles."""
        resp = self.client.get("/api/organizations/agents/")
        names = {r["full_name"] for r in resp.data["results"]}
        self.assertNotIn("Buyer Agent List", names)

    def test_org_scoped_unlike_buyer_list(self):
        """The specific fix this view exists for — unlike
        BuyerListView, an agent from a DIFFERENT org must never
        appear here."""
        other_org = Organization.objects.create(name="Org Lain Agent List")
        other_agent = CustomUser.objects.create_user(
            email="agent.other.agentlist@test.id", password="pass12345!",
            full_name="Agent Org Lain", role="agent",
        )
        OrganizationMembership.objects.create(
            organization=other_org, user=other_agent, role="member", is_active=True,
        )
        resp = self.client.get("/api/organizations/agents/")
        names = {r["full_name"] for r in resp.data["results"]}
        self.assertNotIn("Agent Org Lain", names)

    def test_agent_can_list_agents_too(self):
        """An agent picking a colleague to assign a prospect to
        needs this endpoint too, not just developers."""
        self.client.force_authenticate(user=self.agent_a)
        resp = self.client.get("/api/organizations/agents/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_buyer_cannot_access(self):
        self.client.force_authenticate(user=self.buyer)
        resp = self.client.get("/api/organizations/agents/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_with_no_membership_gets_empty_list(self):
        """Documented, acceptable degrade — see AgentListView's own
        get_queryset(): super_admin has no OrganizationMembership at
        all, so this returns empty rather than erroring."""
        admin = CustomUser.objects.create_user(
            email="admin.agentlist@developindo.id", password="pass12345!",
            full_name="Platform Admin", role="super_admin",
        )
        self.client.force_authenticate(user=admin)
        resp = self.client.get("/api/organizations/agents/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)
