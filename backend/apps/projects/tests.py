# =============================================================================
# === backend/apps/projects/tests.py ===
# =============================================================================
"""
DevelopIndo — Cross-Tenant Isolation Tests (apps.projects)

Sprints 4-9 added ten new endpoints to apps/projects/views.py
(evidence upload/verify, assignment, comments, the /my-actions/ feed,
etc.) and zero of them had a dedicated test before this file. This is
the apps.projects equivalent of apps/core/tests.py::CrossTenantIsolationTests
— same Org A / Org B pattern, applied to every endpoint added since
Sprint 4:

  RequirementEvidenceView          (Sprint 8)
  RequirementEvidenceVerifyView    (Sprint 8)
  EvidenceEligibleVerifiersView    (Sprint 8)
  AssignRequirementView            (Sprint 7)
  RequirementCommentView           (Sprint 7)
  ProjectOrgMembersView            (Sprint 7)
  MyActionsView                    (Sprint 9)
  ProjectRequirementUpdateView     (Sprint 1, previously untested)
  ProjectAdvanceView               (Sprint 1, previously untested)
  ProjectIntelligenceView          (Sprint 1, previously untested)

Org A (PT Asri Sentosa, victim) vs Org B (attacker, Dev B). Dev B must
never read, write, or discover the existence of Org A's requirement
statuses, evidence, comments, or assignments — whether by guessing an
ID directly, or via /my-actions/ leaking it implicitly into a feed
that has no pk-based 404 to catch a scoping mistake.

Run with: python manage.py test apps.projects
"""
from datetime import date, timedelta

from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership
from apps.projects.models import (
    PortfolioSnapshot,
    Project,
    ProjectRequirementStatus,
    RequirementComment,
    RequirementEvidence,
    ReadinessSnapshot,
    StageRequirement,
) 


class ProjectsCrossTenantIsolationTests(APITestCase):
    def setUp(self):
        # ── Shared StageRequirement catalog (not tenant-scoped — global) ──
        self.req_kontraktor, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor",
            defaults={
                "is_mandatory": True,
                "weight": 60,
                "category": StageRequirement.Category.GENERAL,
            },
        )

        # ── Org A — the victim ──────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sentosa")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a@test.id", password="pass12345!",
            full_name="Dev A", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        self.project_a = Project.objects.create(
            organization=self.org_a, name="Cluster A", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.req_status_a = ProjectRequirementStatus.objects.create(
            project=self.project_a,
            requirement=self.req_kontraktor,
            status=ProjectRequirementStatus.Status.IN_PROGRESS,
            due_date=date.today() + timedelta(days=10),
        )
        self.evidence_a = RequirementEvidence.objects.create(
            requirement_status=self.req_status_a,
            file_name="kontrak_a.pdf",
            file_url="https://example.com/kontrak_a.pdf",
            uploaded_by=self.dev_a,
            verification_status=RequirementEvidence.VerificationStatus.PENDING,
        )
        self.comment_a = RequirementComment.objects.create(
            requirement_status=self.req_status_a,
            author=self.dev_a,
            body="Kontrak sudah ditandatangani, menunggu review.",
        )

        # ── Org B — the attacker ─────────────────────────────────────
        self.org_b = Organization.objects.create(name="Griya Makmur")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b@test.id", password="pass12345!",
            full_name="Dev B", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )
        # Org B needs its own project so /my-actions/ has something
        # legitimate to compare against — proves filtering, not just
        # an empty result from having no data at all.
        self.project_b = Project.objects.create(
            organization=self.org_b, name="Cluster B", location="Bekasi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.req_status_b = ProjectRequirementStatus.objects.create(
            project=self.project_b,
            requirement=self.req_kontraktor,
            status=ProjectRequirementStatus.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Project detail / advance / intelligence ───────────────────

    def test_dev_b_cannot_read_dev_a_project_detail(self):
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/projects/{self.project_a.id}/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_dev_b_cannot_read_dev_a_project_intelligence(self):
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/projects/{self.project_a.id}/intelligence/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_dev_b_cannot_advance_dev_a_project_stage(self):
        self._login_as(self.dev_b)
        resp = self.client.post(f"/api/projects/{self.project_a.id}/advance/", {}, format="json")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.project_a.refresh_from_db()
        self.assertEqual(self.project_a.stage, Project.Stage.CONSTRUCTION)

    # ── Requirement status update ─────────────────────────────────

    def test_dev_b_cannot_update_dev_a_requirement_status(self):
        self._login_as(self.dev_b)
        resp = self.client.put(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/",
            {"status": "completed"}, format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.req_status_a.refresh_from_db()
        self.assertNotEqual(self.req_status_a.status, ProjectRequirementStatus.Status.COMPLETED)

    def test_dev_b_cannot_update_dev_a_requirement_via_own_project_id_mismatch(self):
        """Guard against pk/req_status_id mismatch tricks: pass Org A's
        project pk with Org B's own req_status_id, and vice versa — both
        must fail, not silently resolve to whichever one IS accessible."""
        self._login_as(self.dev_b)
        # Org B's project id + Org A's req_status_id (cross-wired)
        resp = self.client.put(
            f"/api/projects/{self.project_b.id}/requirements/{self.req_status_a.id}/",
            {"status": "completed"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.req_status_a.refresh_from_db()
        self.assertNotEqual(self.req_status_a.status, ProjectRequirementStatus.Status.COMPLETED)

    # ── Evidence (Sprint 8) ────────────────────────────────────────

    def test_dev_b_cannot_list_dev_a_evidence(self):
        self._login_as(self.dev_b)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/evidence/"
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_dev_b_cannot_upload_evidence_to_dev_a_requirement(self):
        self._login_as(self.dev_b)
        resp = self.client.post(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/evidence/",
            {"file_url": "https://example.com/sneaky.pdf"}, format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.assertEqual(self.req_status_a.evidence.count(), 1)  # still just evidence_a

    def test_dev_b_cannot_verify_dev_a_evidence(self):
        """Even though Dev B isn't the uploader (so self-verify guard
        wouldn't block them), org membership must block them first."""
        self._login_as(self.dev_b)
        resp = self.client.put(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}"
            f"/evidence/{self.evidence_a.id}/verify/",
            {"action": "approve"}, format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.evidence_a.refresh_from_db()
        self.assertEqual(
            self.evidence_a.verification_status,
            RequirementEvidence.VerificationStatus.PENDING,
        )

    def test_dev_b_cannot_view_eligible_verifiers_for_dev_a_evidence(self):
        self._login_as(self.dev_b)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}"
            f"/evidence/{self.evidence_a.id}/eligible-verifiers/"
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    # ── Assignment + due dates (Sprint 7) ───────────────────────────

    def test_dev_b_cannot_assign_dev_a_requirement(self):
        self._login_as(self.dev_b)
        resp = self.client.put(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/assign/",
            {"assigned_to": str(self.dev_b.id)}, format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.req_status_a.refresh_from_db()
        self.assertIsNone(self.req_status_a.assigned_to)

    def test_dev_b_cannot_set_due_date_on_dev_a_requirement(self):
        self._login_as(self.dev_b)
        resp = self.client.put(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/assign/",
            {"due_date": "2026-12-31"}, format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_dev_b_cannot_list_dev_a_org_members(self):
        """Org member list is used to populate assignee dropdowns —
        must not leak Org A's developer roster to Org B."""
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/projects/{self.project_a.id}/org-members/")
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    # ── Comments (Sprint 7) ──────────────────────────────────────────

    def test_dev_b_cannot_read_dev_a_requirement_comments(self):
        self._login_as(self.dev_b)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/comments/"
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_dev_b_cannot_post_comment_on_dev_a_requirement(self):
        self._login_as(self.dev_b)
        resp = self.client.post(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/comments/",
            {"body": "Sneaky comment from Org B"}, format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.assertEqual(self.req_status_a.comments.count(), 1)  # still just comment_a

    # ── Portfolio + My Actions (Sprint 9) ─────────────────────────────

    def test_dev_b_portfolio_excludes_dev_a_projects(self):
        self._login_as(self.dev_b)
        resp = self.client.get("/api/projects/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [p["id"] for p in resp.data["results"]]
        self.assertNotIn(str(self.project_a.id), ids)
        self.assertIn(str(self.project_b.id), ids)

    def test_dev_b_my_actions_excludes_dev_a_requirements(self):
        """The most important Sprint 9 check: MyActionsView iterates
        Project.objects.for_user(user) internally rather than taking pk
        from the URL, so this is the one place a scoping mistake could
        silently leak cross-org requirement names/ids into a feed —
        with no explicit 404 to catch it, just wrong data in a 200."""
        self._login_as(self.dev_b)
        resp = self.client.get("/api/projects/my-actions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        all_project_ids = {
            item["project_id"]
            for item in resp.data["my_tasks"] + resp.data["unassigned"]
        }
        self.assertNotIn(str(self.project_a.id), all_project_ids)
        all_requirement_ids = {
            item["requirement_id"]
            for item in resp.data["my_tasks"] + resp.data["unassigned"]
        }
        self.assertNotIn(str(self.req_kontraktor.id), all_requirement_ids - {None}) \
            if False else None  # requirement_id is StageRequirement id, shared catalog — skip
        # Stronger check: no status_id belonging to req_status_a leaks through
        all_status_ids = {
            item["status_id"]
            for item in resp.data["my_tasks"] + resp.data["unassigned"]
        }
        self.assertNotIn(str(self.req_status_a.id), all_status_ids)

    def test_dev_b_my_actions_includes_own_unassigned_requirement(self):
        """Sanity check: the fix doesn't break the actual feature —
        Org B's own actionable, unassigned requirement should surface."""
        self._login_as(self.dev_b)
        resp = self.client.get("/api/projects/my-actions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        all_status_ids = {
            item["status_id"]
            for item in resp.data["my_tasks"] + resp.data["unassigned"]
        }
        self.assertIn(str(self.req_status_b.id), all_status_ids)

    # ── Sanity check: Dev A can still do everything above on own data ──

    def test_dev_a_can_still_read_and_write_own_requirement_evidence_comments(self):
        """The isolation fix (if any is needed) must not break legitimate
        same-org access to any endpoint covered above."""
        self._login_as(self.dev_a)

        resp = self.client.get(f"/api/projects/{self.project_a.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/evidence/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/requirements/{self.req_status_a.id}/comments/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

        resp = self.client.get("/api/projects/my-actions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        all_status_ids = {
            item["status_id"]
            for item in resp.data["my_tasks"] + resp.data["unassigned"]
        }
        self.assertIn(str(self.req_status_a.id), all_status_ids)

class ReadinessSnapshotTests(APITestCase):
    """
    Sprint 10: ReadinessSnapshot isolation + correctness.

    Covers:
    - Tenant isolation on /readiness-history/ endpoint
    - snapshot_readiness() writes to ReadinessSnapshot
    - snapshot_readiness() uses update_or_create (no duplicate rows per day)
    - History endpoint returns data in correct date order
    - Empty history (no snapshots yet) returns empty results, not 500
    """

    def setUp(self):
        # ── Org A ──────────────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sentosa Sprint10")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a.s10@test.id", password="pass12345!",
            full_name="Dev A S10", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        self.project_a = Project.objects.create(
            organization=self.org_a, name="Cluster A S10", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )

        # ── Org B ──────────────────────────────────────────────
        self.org_b = Organization.objects.create(name="Griya Makmur Sprint10")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b.s10@test.id", password="pass12345!",
            full_name="Dev B S10", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Isolation ─────────────────────────────────────────────

    def test_dev_b_cannot_read_dev_a_readiness_history(self):
        """Core isolation: the readiness-history endpoint must not
        expose Org A's score data to Org B's developer."""
        # Seed a snapshot for Org A
        ReadinessSnapshot.objects.create(
            project=self.project_a, score=40, snapped_at=date.today(),
        )
        self._login_as(self.dev_b)
        resp = self.client.get(f"/api/projects/{self.project_a.id}/readiness-history/")
        self.assertIn(
            resp.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )

    # ── snapshot_readiness() correctness ──────────────────────

    def test_snapshot_readiness_writes_readiness_snapshot_row(self):
        """snapshot_readiness() must create a ReadinessSnapshot row
        for today so the trend chart has data."""
        self.assertEqual(
            ReadinessSnapshot.objects.filter(project=self.project_a).count(), 0
        )
        self.project_a.snapshot_readiness()
        self.assertEqual(
            ReadinessSnapshot.objects.filter(project=self.project_a).count(), 1
        )

    def test_snapshot_readiness_is_idempotent_within_same_day(self):
        """Calling snapshot_readiness() twice on the same day must not
        create duplicate rows — update_or_create enforces uniqueness."""
        self.project_a.snapshot_readiness()
        self.project_a.snapshot_readiness()
        self.assertEqual(
            ReadinessSnapshot.objects.filter(project=self.project_a).count(), 1
        )

    # ── Endpoint correctness ───────────────────────────────────

    def test_readiness_history_returns_results_in_date_order(self):
        """History must come back oldest-first so the frontend line
        chart renders left-to-right without any client-side sort."""
        today     = date.today()
        yesterday = today - timedelta(days=1)
        ReadinessSnapshot.objects.create(project=self.project_a, score=52, snapped_at=today)
        ReadinessSnapshot.objects.create(project=self.project_a, score=40, snapped_at=yesterday)

        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/readiness-history/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dates  = [r["date"] for r in resp.data["results"]]
        scores = [r["score"] for r in resp.data["results"]]
        self.assertEqual(dates,  [yesterday.isoformat(), today.isoformat()])
        self.assertEqual(scores, [40, 52])

    def test_readiness_history_empty_returns_200_not_500(self):
        """If no snapshots exist yet (first run, no data), the endpoint
        must return an empty results list, never a 500."""
        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/readiness-history/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["results"], [])

class DependencyGraphTests(APITestCase):
    """
    Sprint 11: Dependency graph endpoint isolation + correctness.
    """

    def setUp(self):
        from apps.projects.models import StageRequirement, ProjectRequirementStatus
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor S11",
            defaults={"is_mandatory": True, "weight": 60},
        )

        self.org_a = Organization.objects.create(name="Asri S11 A")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a.s11@test.id", password="pass12345!",
            full_name="Dev A S11", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        self.project_a = Project.objects.create(
            organization=self.org_a, name="Cluster A S11", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )

        self.org_b = Organization.objects.create(name="Griya S11 B")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b.s11@test.id", password="pass12345!",
            full_name="Dev B S11", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_dev_b_cannot_read_dev_a_dependency_graph(self):
        self._login_as(self.dev_b)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/dependency-graph/"
        )
        self.assertIn(
            resp.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )

    def test_dev_a_dependency_graph_returns_nodes_and_edges(self):
        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/dependency-graph/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertIn("nodes", resp.data)
        self.assertIn("edges", resp.data)
        self.assertIsInstance(resp.data["nodes"], list)
        self.assertIsInstance(resp.data["edges"], list)
        if resp.data["nodes"]:
            node = resp.data["nodes"][0]
            for field in ("id", "name", "status", "is_mandatory",
                          "is_blocking", "is_dependency_blocked", "weight_pct"):
                self.assertIn(field, node)

class ActionChainAndActivityFilterTests(APITestCase):
    """
    Sprint 12: Action chain + activity timeline filter isolation + correctness.

    Covers:
    - action_chain is present in intelligence for a blocked project
    - action_chain is None when project has no blockers
    - Dev B cannot filter Dev A's activity timeline (tenant isolation)
    """

    def setUp(self):
        from apps.projects.models import (
            ProjectRequirementStatus,
            StageRequirement,
        )
        # ── Shared requirement ──────────────────────────────────────
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor S12",
            defaults={"is_mandatory": True, "weight": 60},
        )

        # ── Org A — the victim ──────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sentosa Sprint12")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a.s12@test.id", password="pass12345!",
            full_name="Dev A S12", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        # Blocked project: has a mandatory requirement that is PENDING
        self.project_blocked = Project.objects.create(
            organization=self.org_a, name="Cluster Blocked S12", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        # Requirement status = PENDING (blocking)
        self.req_status = ProjectRequirementStatus.objects.create(
            project=self.project_blocked,
            requirement=self.req,
            status=ProjectRequirementStatus.Status.PENDING,
        )

        # ── Org B — the attacker ─────────────────────────────────────
        self.org_b = Organization.objects.create(name="Griya Sprint12")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b.s12@test.id", password="pass12345!",
            full_name="Dev B S12", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Action chain correctness ──────────────────────────────────

    def test_action_chain_present_for_blocked_project(self):
        """
        Sprint 12: intelligence summary must include a non-null action_chain
        when the project has a pending mandatory requirement blocking the stage.
        The chain must have the correct structure.
        """
        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_blocked.id}/intelligence/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        chain = resp.data["intelligence"].get("action_chain")
        self.assertIsNotNone(chain, "action_chain should be non-null for blocked project")
        self.assertIn("steps",              chain)
        self.assertIn("total_steps",        chain)
        self.assertIn("completed_steps",    chain)
        self.assertIn("requirement_name",   chain)
        self.assertIn("est_remaining_minutes", chain)
        self.assertIsInstance(chain["steps"], list)
        self.assertGreater(len(chain["steps"]), 0)
        # First step must be "assign" type since req_status has no assigned_to
        first_step = chain["steps"][0]
        self.assertEqual(first_step["action_type"], "assign")
        self.assertFalse(first_step["is_done"])

    def test_action_chain_is_none_when_no_blockers(self):
        """
        Sprint 12: action_chain must be None when all mandatory requirements
        are completed — no blockers, nothing to chain.
        """
        # Mark the requirement as completed
        from apps.projects.models import ProjectRequirementStatus
        self.req_status.status = ProjectRequirementStatus.Status.COMPLETED
        self.req_status.save()

        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_blocked.id}/intelligence/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        chain = resp.data["intelligence"].get("action_chain")
        self.assertIsNone(chain, "action_chain should be None when no blockers exist")

    # ── Activity filter isolation ──────────────────────────────────

    def test_dev_b_cannot_filter_dev_a_activity_timeline(self):
        """
        Sprint 12: the new ?type= filter must not open a new cross-tenant
        attack surface. Dev B cannot read Dev A's filtered activity feed
        any more than the unfiltered one.
        """
        self._login_as(self.dev_b)
        for filter_type in ("all", "evidence", "readiness", "assignments", "comments"):
            resp = self.client.get(
                f"/api/projects/{self.project_blocked.id}/activity/?type={filter_type}"
            )
            self.assertIn(
                resp.status_code,
                (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
                f"Dev B should be blocked for type={filter_type}",
            )

class DecisionEngineTests(APITestCase):
    """
    Sprint 13: Decision Engine isolation + correctness.

    Covers:
    - Tenant isolation on /decision/ endpoint
    - Returns primary recommendation for a blocked project
    - Returns all_clear when no mandatory requirements are pending
    """

    def setUp(self):
        from apps.projects.models import (
            ProjectRequirementStatus,
            StageRequirement,
        )
        # ── Shared requirement ──────────────────────────────────────
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor S13",
            defaults={"is_mandatory": True, "weight": 60},
        )

        # ── Org A — victim ──────────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sentosa Sprint13")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a.s13@test.id", password="pass12345!",
            full_name="Dev A S13", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        # Blocked project: mandatory requirement is PENDING
        self.project_blocked = Project.objects.create(
            organization=self.org_a, name="Cluster Blocked S13", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.req_status = ProjectRequirementStatus.objects.create(
            project=self.project_blocked,
            requirement=self.req,
            status=ProjectRequirementStatus.Status.PENDING,
        )

        # ── Org B — attacker ─────────────────────────────────────────
        self.org_b = Organization.objects.create(name="Griya Sprint13")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b.s13@test.id", password="pass12345!",
            full_name="Dev B S13", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Isolation ─────────────────────────────────────────────

    def test_dev_b_cannot_read_dev_a_decision_engine(self):
        """
        Sprint 13: /decision/ endpoint must not expose Org A's
        recommendation data to Org B's developer.
        """
        self._login_as(self.dev_b)
        resp = self.client.get(
            f"/api/projects/{self.project_blocked.id}/decision/"
        )
        self.assertIn(
            resp.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )

    # ── Correctness ───────────────────────────────────────────

    def test_decision_engine_returns_primary_for_blocked_project(self):
        """
        Sprint 13: when a project has a pending mandatory requirement,
        the Decision Engine must return has_recommendations=True with
        a valid primary recommendation and correct structure.
        """
        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_blocked.id}/decision/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["has_recommendations"])
        self.assertFalse(resp.data["all_clear"])

        primary = resp.data["primary"]
        self.assertIsNotNone(primary)
        # Must name the blocking requirement
        self.assertEqual(primary["requirement_name"], self.req.name)
        # readiness_impact_pct must equal the requirement's weight_pct
        self.assertGreater(primary["readiness_impact_pct"], 0)
        # Must have reasons
        self.assertIsInstance(primary["reasons"], list)
        self.assertGreater(len(primary["reasons"]), 0)
        # Projected readiness must be higher than current
        self.assertGreater(
            resp.data["projected_readiness"],
            resp.data["current_readiness"],
        )
        # Must have priority field
        self.assertIn(primary["priority"], ("high", "medium", "low"))

    def test_decision_engine_all_clear_when_no_blockers(self):
        """
        Sprint 13: when all mandatory requirements are completed,
        has_recommendations must be False and all_clear must be True.
        """
        from apps.projects.models import ProjectRequirementStatus
        # Complete the requirement so nothing is blocking
        self.req_status.status = ProjectRequirementStatus.Status.COMPLETED
        self.req_status.save()

        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_blocked.id}/decision/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["has_recommendations"])
        self.assertTrue(resp.data["all_clear"])
        self.assertIsNone(resp.data["primary"])
        self.assertEqual(resp.data["alternatives"], [])

class RiskForecastTests(APITestCase):
    """
    Sprint 14: Risk Forecast isolation + correctness.

    Covers:
    - Tenant isolation on /risk-forecast/ endpoint
    - Forecast score >= current for a project already past its end_date
      (timeline_overrun factor grows with time — can't shrink)
    - Forecast == current for a brand-new project with no time-based factors
      (no overrun, no payment overdue, no permit rejections)
    """

    def setUp(self):
        # ── Org A — victim ──────────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sentosa Sprint14")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a.s14@test.id", password="pass12345!",
            full_name="Dev A S14", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )

        # Overdue project — end_date in the past → timeline_overrun active
        self.project_overdue = Project.objects.create(
            organization=self.org_a, name="Cluster Overdue S14", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),   # well in the past
        )

        # Fresh project — end_date in the future → no time-based risk factors
        self.project_fresh = Project.objects.create(
            organization=self.org_a, name="Cluster Fresh S14", location="Bekasi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2026, 1, 1),
            end_date=date(2030, 12, 31),   # far in the future
        )

        # ── Org B — attacker ─────────────────────────────────────────
        self.org_b = Organization.objects.create(name="Griya Sprint14")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b.s14@test.id", password="pass12345!",
            full_name="Dev B S14", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Isolation ─────────────────────────────────────────────

    def test_dev_b_cannot_read_dev_a_risk_forecast(self):
        """
        Sprint 14: /risk-forecast/ endpoint must not expose Org A's
        risk projection data to Org B's developer.
        """
        self._login_as(self.dev_b)
        resp = self.client.get(
            f"/api/projects/{self.project_overdue.id}/risk-forecast/"
        )
        self.assertIn(
            resp.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )

    # ── Correctness ───────────────────────────────────────────

    def test_risk_forecast_score_gte_current_for_overdue_project(self):
        """
        Sprint 14: For a project already past its end_date, the forecast
        score must be >= the current score. timeline_overrun points can only
        stay the same or increase (they're capped at 20pts max), never decrease.

        Also verifies the response structure is correct.
        """
        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_overdue.id}/risk-forecast/?days=14"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        # Forecast score must be >= current (time-based factors can only grow)
        self.assertGreaterEqual(
            resp.data["forecast"]["score"],
            resp.data["current"]["score"],
        )
        # Delta must be non-negative
        self.assertGreaterEqual(resp.data["delta"], 0)

        # Response structure check
        for field in ("current", "forecast", "delta", "will_escalate", "top_drivers", "days"):
            self.assertIn(field, resp.data, f"Missing field: {field}")
        self.assertEqual(resp.data["days"], 14)

        # top_drivers must be a list
        self.assertIsInstance(resp.data["top_drivers"], list)
        if resp.data["top_drivers"]:
            driver = resp.data["top_drivers"][0]
            for f in ("key", "name", "current_points", "forecast_points", "delta_points", "is_new"):
                self.assertIn(f, driver, f"Missing driver field: {f}")

    def test_risk_forecast_equals_current_for_no_time_factors(self):
        """
        Sprint 14: For a fresh project with no overrun and no payment overdue,
        the forecast score must equal the current score.
        The reference_date param doesn't change anything if no time-sensitive
        factors are active — deterministic and honest.
        """
        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_fresh.id}/risk-forecast/?days=14"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # No time-based factors → forecast == current
        self.assertEqual(
            resp.data["forecast"]["score"],
            resp.data["current"]["score"],
        )
        self.assertEqual(resp.data["delta"], 0)
        self.assertFalse(resp.data["will_escalate"])

class CauseEffectAndInteractiveDependencyTests(APITestCase):
    """
    Sprint 16: Cause & Effect impact capture + Interactive Dependency Graph.

    Covers:
    - Impact fields (readiness_before/after, risk_before/after) are stored
      in RequirementAudit when a requirement is updated
    - activity_timeline() returns readiness_delta and risk_delta
    - dependency_graph nodes include block_reason, assigned_to_name, est_minutes
    """

    def setUp(self):
        from apps.projects.models import (
            ProjectRequirementStatus,
            StageRequirement,
        )
        # ── Shared requirement ──────────────────────────────────────
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor S16",
            defaults={"is_mandatory": True, "weight": 60},
        )

        # ── Org + project setup ─────────────────────────────────────
        self.org  = Organization.objects.create(name="Asri Sprint16")
        self.user = CustomUser.objects.create_user(
            email="dev.s16@test.id", password="pass12345!",
            full_name="Dev S16", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster S16", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.req_status = ProjectRequirementStatus.objects.create(
            project=self.project,
            requirement=self.req,
            status=ProjectRequirementStatus.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Impact capture correctness ─────────────────────────────────

    def test_impact_fields_captured_on_requirement_update(self):
        """
        Sprint 16: when a requirement status is updated, the most recent
        RequirementAudit entry must have readiness_before and readiness_after
        set (not None). This proves the impact capture loop is working.
        """
        from apps.projects.models import RequirementAudit
        self._login_as(self.user)

        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/",
            {"status": "in_progress"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        # The most recent audit log must have impact fields stored
        latest_log = self.req_status.audit_logs.first()
        self.assertIsNotNone(latest_log, "Audit log should exist after update")
        self.assertIsNotNone(
            latest_log.readiness_before,
            "readiness_before should be stored after Sprint 16"
        )
        self.assertIsNotNone(
            latest_log.readiness_after,
            "readiness_after should be stored after Sprint 16"
        )
        self.assertIsNotNone(latest_log.risk_before)
        self.assertIsNotNone(latest_log.risk_after)

    def test_activity_timeline_includes_impact_data(self):
        """
        Sprint 16: activity_timeline() must include readiness_delta and
        risk_delta in each activity item after the update creates an
        impact-aware audit log.
        """
        from apps.projects.models import RequirementAudit
        self._login_as(self.user)

        # Perform an update to generate an impact-aware audit log
        self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/",
            {"status": "in_progress"},
            format="json",
        )

        # Fetch activity timeline
        resp = self.client.get(f"/api/projects/{self.project.id}/activity/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resp.data["results"]), 0)

        # Most recent activity must have the new fields (even if delta is 0)
        latest = resp.data["results"][0]
        self.assertIn("readiness_delta", latest, "readiness_delta missing from activity")
        self.assertIn("risk_delta",      latest, "risk_delta missing from activity")

    def test_dependency_graph_node_includes_detail_fields(self):
        """
        Sprint 16: dependency graph nodes must include block_reason,
        assigned_to_name, and est_minutes for the interactive detail panel.
        """
        self._login_as(self.user)
        resp = self.client.get(
            f"/api/projects/{self.project.id}/dependency-graph/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        if resp.data["nodes"]:
            node = resp.data["nodes"][0]
            # Sprint 16 fields must be present
            self.assertIn("block_reason",     node, "block_reason missing from node")
            self.assertIn("assigned_to_name", node, "assigned_to_name missing from node")
            self.assertIn("est_minutes",      node, "est_minutes missing from node")
            # est_minutes must be a positive integer
            self.assertIsInstance(node["est_minutes"], int)
            self.assertGreater(node["est_minutes"], 0)

class LivePulseAndEventStreamTests(APITestCase):
    """
    Sprint 17: Pulse endpoint + cross-project event stream isolation + correctness.

    Covers:
    - Tenant isolation on /pulse/ endpoint
    - /pulse/ returns has_updates=False when nothing changed since timestamp
    - /recent-activity/ excludes events from other orgs (cross-tenant isolation)
    """

    def setUp(self):
        # ── Org A — victim ──────────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sprint17")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a.s17@test.id", password="pass12345!",
            full_name="Dev A S17", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        self.project_a = Project.objects.create(
            organization=self.org_a, name="Cluster A S17", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )

        # ── Org B — attacker ─────────────────────────────────────────
        self.org_b = Organization.objects.create(name="Griya Sprint17")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b.s17@test.id", password="pass12345!",
            full_name="Dev B S17", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )
        self.project_b = Project.objects.create(
            organization=self.org_b, name="Cluster B S17", location="Jakarta",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Pulse isolation ───────────────────────────────────────────

    def test_dev_b_cannot_poll_dev_a_project_pulse(self):
        """
        Sprint 17: the /pulse/ endpoint must not expose Org A's
        live event data to Org B's developer.
        """
        self._login_as(self.dev_b)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/pulse/"
        )
        self.assertIn(
            resp.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )

    # ── Pulse correctness ─────────────────────────────────────────

    def test_pulse_returns_no_updates_when_nothing_changed(self):
        """
        Sprint 17: polling with a future 'since' timestamp (nothing happened
        after that point) must return has_updates=False and empty new_events.
        This is the critical check that prevents unnecessary re-renders.
        """
        from django.utils import timezone
        # Use a timestamp 1 hour in the future — nothing can have happened after it
        future = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        self._login_as(self.dev_a)
        resp = self.client.get(
            f"/api/projects/{self.project_a.id}/pulse/?since={future}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertFalse(resp.data["has_updates"], "has_updates should be False when nothing changed")
        self.assertEqual(len(resp.data["new_events"]), 0)
        # But score and metadata should still be present
        self.assertIn("readiness_score",   resp.data)
        self.assertIn("blocking_count",    resp.data)
        self.assertIn("checked_at",        resp.data)

    # ── Recent activity isolation ─────────────────────────────────

    def test_recent_activity_excludes_other_org_events(self):
        """
        Sprint 17: /recent-activity/ must return ONLY events from the
        requesting user's org. Dev B must not see Dev A's project events
        in the cross-project feed — even via the aggregated endpoint.
        """
        from apps.projects.models import RequirementAudit, StageRequirement, ProjectRequirementStatus

        # Create a requirement and audit log for Org A's project
        req_a, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor S17A",
            defaults={"is_mandatory": True, "weight": 60},
        )
        req_status_a = ProjectRequirementStatus.objects.create(
            project=self.project_a, requirement=req_a,
            status=ProjectRequirementStatus.Status.IN_PROGRESS,
        )
        RequirementAudit.log(
            requirement_status=req_status_a,
            action=RequirementAudit.Action.UPDATED,
            changed_by=self.dev_a,
            old_value="pending",
            new_value="in_progress",
        )

        # Dev B queries recent-activity — must NOT see Dev A's events
        self._login_as(self.dev_b)
        resp = self.client.get("/api/projects/recent-activity/?limit=20")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        project_ids_in_feed = {e["project_id"] for e in resp.data["results"]}
        self.assertNotIn(
            str(self.project_a.id),
            project_ids_in_feed,
            "Org A's project events must not appear in Org B's recent-activity feed",
        )

# SPRINT 18 - Portfolio Intelligence Hub (CEO Bloomberg View)
class PortfolioIntelligenceTests(APITestCase):
    """
    Sprint 18: Portfolio Intelligence Hub isolation + correctness.

    Covers:
    - Tenant isolation: Dev B cannot read Dev A's portfolio intelligence
    - Metrics computed correctly from project data
    - snapshot_portfolio_daily management command writes correct values
    """

    def setUp(self):
        # ── Org A — victim ──────────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sprint18")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a.s18@test.id", password="pass12345!",
            full_name="Dev A S18", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        # Two projects for Org A
        self.project_a1 = Project.objects.create(
            organization=self.org_a, name="Cluster A1 S18", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),  # overdue
            target_budget=16_000_000_000,
        )
        self.project_a2 = Project.objects.create(
            organization=self.org_a, name="Cluster A2 S18", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2026, 1, 1), end_date=date(2027, 12, 31),  # not overdue
            target_budget=20_000_000_000,
        )

        # ── Org B — attacker ─────────────────────────────────────────
        self.org_b = Organization.objects.create(name="Griya Sprint18")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.b.s18@test.id", password="pass12345!",
            full_name="Dev B S18", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Isolation ─────────────────────────────────────────────

    def test_dev_b_cannot_read_dev_a_portfolio_intelligence(self):
        """
        Sprint 18: /portfolio-intelligence/ must return only Org B's
        data when Dev B queries it. Dev A's project counts/metrics
        must never appear in Dev B's response.
        """
        self._login_as(self.dev_b)
        resp = self.client.get("/api/projects/portfolio-intelligence/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Dev B has no projects — should see zeros, not Org A's data
        self.assertEqual(
            resp.data["current"]["total_projects"], 0,
            "Dev B should see 0 projects, not Org A's project count"
        )

    # ── Correctness ───────────────────────────────────────────

    def test_portfolio_intelligence_computes_metrics_correctly(self):
        """
        Sprint 18: current metrics must accurately reflect the
        actual project state for the org.
        """
        self._login_as(self.dev_a)
        resp = self.client.get("/api/projects/portfolio-intelligence/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

        current = resp.data["current"]
        # 2 projects for Org A
        self.assertEqual(current["total_projects"], 2)
        # delayed_count: only project_a1 has end_date in the past
        self.assertGreaterEqual(current["delayed_count"], 1)
        # revenue_protected: both projects are in CONSTRUCTION (active)
        # = 16B + 20B = 36B (or close to it depending on Rupiah conversion)
        self.assertGreater(current["revenue_protected"], 0)
        # avg_readiness should be a valid percentage
        self.assertGreaterEqual(current["avg_readiness"], 0)
        self.assertLessEqual(current["avg_readiness"], 100)
        # top_at_risk should be a list
        self.assertIsInstance(resp.data["top_at_risk"], list)
        # has_history: false until snapshot_portfolio_daily runs
        self.assertFalse(resp.data["has_history"])
        # week_delta: null until snapshot history exists
        self.assertIsNone(resp.data["week_delta"])

    # ── Management command ────────────────────────────────────

    def test_snapshot_portfolio_daily_writes_correct_values(self):
        """
        Sprint 18: the management command must write a PortfolioSnapshot
        row with correct values for Org A's projects.
        """
        from apps.projects.models import PortfolioSnapshot
        from django.core.management import call_command

        # Verify no snapshot exists before running
        self.assertEqual(
            PortfolioSnapshot.objects.filter(organization=self.org_a).count(), 0
        )

        # Run the management command
        call_command("snapshot_portfolio_daily", verbosity=0)

        # Verify snapshot was written for Org A
        snap = PortfolioSnapshot.objects.filter(
            organization=self.org_a,
            snapped_at=date.today(),
        ).first()
        self.assertIsNotNone(snap, "PortfolioSnapshot should exist after running command")
        self.assertEqual(snap.total_projects, 2)
        self.assertGreater(snap.revenue_protected, 0)
        # avg_readiness should be between 0 and 100
        self.assertGreaterEqual(snap.avg_readiness, 0)
        self.assertLessEqual(snap.avg_readiness, 100)

# =============================================================================
# BUGFIX — blocking_count / stage_can_advance integrity
# =============================================================================
class StageAdvancementIntegrityTests(APITestCase):
    """
    Regression suite for a bug found via prod screenshots (Cluster C):
    a mandatory requirement sitting in AWAITING_VERIFICATION (evidence
    uploaded, not yet verified) was NOT counted as blocking — letting
    blocking_count report 0, can_advance report True, and the Decision
    Engine banner falsely declare "Semua requirement wajib sudah selesai!"

    Root cause: blocking_count only checked for PENDING/IN_PROGRESS,
    silently excluding AWAITING_VERIFICATION from the blocking check.

    Covers:
    - Model-level: blocking_count / can_advance correctness at each status
    - API-level: /requirements/<id>/ PUT response reflects the same truth
    - Tenant isolation: unaffected by this bug, but re-confirmed here
    """

    def setUp(self):
        # ── Shared mandatory requirement ─────────────────────────────
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor Integrity Check",
            defaults={"is_mandatory": True, "weight": 60},
        )

        # ── Org A — victim ────────────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sentosa Integrity")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.a.integrity@test.id", password="pass12345!",
            full_name="Dev A Integrity", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org_a, name="Cluster Integrity", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.req_status = ProjectRequirementStatus.objects.create(
            project=self.project,
            requirement=self.req,
            status=ProjectRequirementStatus.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    # ── Model-level correctness ─────────────────────────────────────

    def test_awaiting_verification_counts_as_blocking(self):
        """
        THE regression test. Uploading evidence (→ AWAITING_VERIFICATION)
        must NOT clear a mandatory requirement's blocking status.
        """
        self.req_status.mark_awaiting_verification(user=self.dev_a)

        self.assertEqual(
            self.project.blocking_count, 1,
            "AWAITING_VERIFICATION requirement must still count as blocking"
        )
        self.assertFalse(
            self.project.can_advance,
            "Project must not be advanceable while evidence is unverified"
        )

    def test_pending_requirement_blocks(self):
        """Control case: PENDING must always block (sanity check)."""
        self.assertEqual(self.project.blocking_count, 1)
        self.assertFalse(self.project.can_advance)

    def test_in_progress_requirement_blocks(self):
        """Control case: IN_PROGRESS must always block (sanity check)."""
        self.req_status.status = ProjectRequirementStatus.Status.IN_PROGRESS
        self.req_status.save()
        self.assertEqual(self.project.blocking_count, 1)
        self.assertFalse(self.project.can_advance)

    def test_completed_requirement_does_not_block(self):
        """Control case: only COMPLETED actually clears the block."""
        self.req_status.mark_completed(user=self.dev_a)
        self.assertEqual(self.project.blocking_count, 0)
        self.assertTrue(self.project.can_advance)

    # ── API-level correctness ───────────────────────────────────────

    def test_stage_can_advance_false_in_api_response_when_awaiting_verification(self):
        """
        The /requirements/<id>/ PUT response's impact.stage_can_advance
        must be False when the update results in AWAITING_VERIFICATION —
        this is the exact field the frontend's Decision Engine banner
        and Sprint 20's feedback loop both trust.
        """
        self._login_as(self.dev_a)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/",
            {"status": "menunggu_verifikasi"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(
            resp.data["impact"]["stage_can_advance"],
            "API must not report stage_can_advance=True for unverified evidence"
        )

    def test_stage_can_advance_true_in_api_response_when_completed(self):
        """Control case at the API level: COMPLETED does allow advancement."""
        self._login_as(self.dev_a)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/",
            {"status": "completed"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["impact"]["stage_can_advance"])


# =============================================================================
# UX-POLISH FIX — Decision Engine "awaiting verification" message
# =============================================================================
class DecisionEngineAwaitingVerificationMessageTests(APITestCase):
    """
    UX-polish fix (same session as the blocking_count bug): when a
    mandatory requirement is AWAITING_VERIFICATION and nothing else is
    actionable, the Decision Engine message must name what's actually
    happening ("Menunggu verifikasi: X") instead of the vague
    "Tidak ada tindakan tersedia saat ini." — which reads like nothing
    is happening when in fact something is, just not by the developer.

    Covers:
    - Single item awaiting verification → named in the message
    - Multiple items awaiting verification → all named, comma-separated
    - all_clear / has_recommendations behavior unchanged (message-only fix)
    - Fully COMPLETED → original celebratory message unaffected
    """

    def setUp(self):
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Rencana Kerja Msg",
            defaults={"is_mandatory": True, "weight": 40},
        )
        self.req2, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Site Plan Msg",
            defaults={"is_mandatory": True, "weight": 20},
        )

        self.org = Organization.objects.create(name="Asri Sentosa Msg")
        self.dev = CustomUser.objects.create_user(
            email="dev.msg@test.id", password="pass12345!",
            full_name="Dev Msg", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Msg", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.status1 = ProjectRequirementStatus.objects.create(
            project=self.project, requirement=self.req,
            status=ProjectRequirementStatus.Status.PENDING,
        )
        self.status2 = ProjectRequirementStatus.objects.create(
            project=self.project, requirement=self.req2,
            status=ProjectRequirementStatus.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_message_names_the_requirement_awaiting_verification(self):
        """Single item awaiting verification → named explicitly."""
        self.status1.mark_awaiting_verification(user=self.dev)
        self.status2.mark_completed(user=self.dev)

        self._login_as(self.dev)
        resp = self.client.get(f"/api/projects/{self.project.id}/decision/")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["all_clear"])
        self.assertFalse(resp.data["has_recommendations"])
        self.assertIn("Rencana Kerja Msg", resp.data["message"])
        self.assertNotEqual(
            resp.data["message"], "Tidak ada tindakan tersedia saat ini.",
            "Message must name the pending item, not stay generic"
        )

    def test_message_names_all_requirements_awaiting_verification(self):
        """Multiple items awaiting verification → all named."""
        self.status1.mark_awaiting_verification(user=self.dev)
        self.status2.mark_awaiting_verification(user=self.dev)

        self._login_as(self.dev)
        resp = self.client.get(f"/api/projects/{self.project.id}/decision/")

        self.assertIn("Rencana Kerja Msg", resp.data["message"])
        self.assertIn("Site Plan Msg", resp.data["message"])

    def test_all_clear_message_unaffected_when_truly_complete(self):
        """Control case: the original celebratory message still fires
        correctly when there's genuinely nothing left to verify."""
        self.status1.mark_completed(user=self.dev)
        self.status2.mark_completed(user=self.dev)

        self._login_as(self.dev)
        resp = self.client.get(f"/api/projects/{self.project.id}/decision/")

        self.assertTrue(resp.data["all_clear"])
        self.assertEqual(
            resp.data["message"], "Semua requirement wajib sudah selesai! 🎉"
        )


# =============================================================================
# BUGFIX — Sprint 16 delta capture gap in the evidence upload endpoint
# =============================================================================
class EvidenceUploadImpactCaptureTests(APITestCase):
    """
    Sprint 16 gap found via prod screenshot comparison: the evidence
    upload endpoint (RequirementEvidenceView.post()) was the one
    status-changing code path that never captured readiness_before/
    after or risk_before/after — meaning "mengunggah bukti" events
    NEVER got Cause & Effect delta badges on prod, even though the
    frontend rendering code was 100% correct and complete.

    Root cause: only ProjectRequirementUpdateView.put() wired in the
    before/after snapshot pattern; mark_awaiting_verification() (called
    from the evidence upload flow) and the evidence resubmission log
    call never did.

    Covers:
    - First-time evidence upload → impact fields captured on the log
    - Resubmission after rejection → impact fields captured too
    - activity_timeline() reflects the delta for an evidence-upload event
    """

    def setUp(self):
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor Evidence Impact",
            defaults={"is_mandatory": True, "weight": 60},
        )
        self.org = Organization.objects.create(name="Asri Sentosa Evidence Impact")
        self.dev = CustomUser.objects.create_user(
            email="dev.evimpact@test.id", password="pass12345!",
            full_name="Dev Evidence Impact", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Evidence Impact", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.req_status = ProjectRequirementStatus.objects.create(
            project=self.project,
            requirement=self.req,
            status=ProjectRequirementStatus.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_first_time_evidence_upload_captures_impact(self):
        """
        THE regression test. Uploading evidence for the first time
        (PENDING → AWAITING_VERIFICATION) must produce an audit log
        with readiness_before/after and risk_before/after populated —
        not left as None.
        """
        self._login_as(self.dev)
        resp = self.client.post(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/evidence/",
            {"file_url": "https://example.com/kontrak.pdf"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        latest_log = self.req_status.audit_logs.first()
        self.assertIsNotNone(latest_log)
        self.assertIsNotNone(
            latest_log.readiness_before,
            "readiness_before must be captured on evidence upload, not left None"
        )
        self.assertIsNotNone(
            latest_log.readiness_after,
            "readiness_after must be captured on evidence upload, not left None"
        )
        self.assertIsNotNone(latest_log.risk_before)
        self.assertIsNotNone(latest_log.risk_after)

    def test_activity_timeline_shows_delta_for_evidence_upload_event(self):
        """
        The exact prod symptom: the Activity Timeline entry for
        "mengunggah bukti untuk X" must carry a real readiness_delta,
        not silently fall back to None (which hides the badge on the
        frontend, since the badge only renders when the delta is
        non-null and non-zero).
        """
        self._login_as(self.dev)
        self.client.post(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/evidence/",
            {"file_url": "https://example.com/kontrak.pdf"}, format="json",
        )

        resp = self.client.get(f"/api/projects/{self.project.id}/activity/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(resp.data["results"]), 0)

        latest = resp.data["results"][0]
        self.assertEqual(latest["action"], "evidence_uploaded")
        self.assertIn("readiness_delta", latest)
        self.assertIsNotNone(
            latest["readiness_delta"],
            "readiness_delta must not be None for an evidence-upload event "
            "— this is exactly why delta badges never rendered on prod"
        )

    def test_resubmission_after_rejection_also_captures_impact(self):
        """
        Control case: the OTHER branch inside the evidence view (re-
        upload after a rejection, IN_PROGRESS → AWAITING_VERIFICATION)
        must capture impact fields too, not just the first-upload path.
        """
        self._login_as(self.dev)
        # First upload via the real endpoint
        self.client.post(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/evidence/",
            {"file_url": "https://example.com/kontrak-v1.pdf"}, format="json",
        )
        # Simulate a rejection putting it back to IN_PROGRESS
        self.req_status.refresh_from_db()
        self.req_status.status = ProjectRequirementStatus.Status.IN_PROGRESS
        self.req_status.save(update_fields=["status"])

        # Resubmission — hits the other branch inside the evidence view
        resp = self.client.post(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/evidence/",
            {"file_url": "https://example.com/kontrak-v2.pdf"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        latest_log = self.req_status.audit_logs.first()
        self.assertIsNotNone(latest_log.readiness_before)
        self.assertIsNotNone(latest_log.readiness_after)


# =============================================================================
# BUGFIX — Sprint 16 delta capture gap, part 2: evidence verify/approve
# =============================================================================
class EvidenceVerificationImpactCaptureTests(APITestCase):
    """
    Sprint 16 gap, part 2 — found while explaining why a fresh evidence
    upload showed no badge (that part was CORRECT — a PENDING→
    AWAITING_VERIFICATION transition has a genuine zero delta, since
    only COMPLETED counts toward readiness and blocking_count doesn't
    change either). Tracing that led here: RequirementEvidenceVerifyView
    .put() — the approve/reject endpoint — never captured readiness_
    before/after or risk_before/after. This is actually the MORE
    important gap of the two: approving evidence is what fires
    mark_completed() and genuinely moves readiness up / risk down, so
    it's the one event where Cause & Effect badges should reliably be
    non-zero and visible.

    Covers:
    - Approving evidence captures a genuine, non-zero impact
    - BOTH audit logs approve() creates (COMPLETED + EVIDENCE_APPROVED)
      get patched, not just whichever is "latest"
    - activity_timeline() surfaces the delta for the approval event
    - Rejecting evidence still legitimately produces zero delta
      (status never reaches COMPLETED) — guards against a future
      change that accidentally treats rejection like completion
    - Self-verify guard is untouched by this fix
    """

    def setUp(self):
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor Verify Impact",
            defaults={"is_mandatory": True, "weight": 60},
        )
        self.org = Organization.objects.create(name="Asri Sentosa Verify Impact")
        self.uploader = CustomUser.objects.create_user(
            email="uploader.verifyimpact@test.id", password="pass12345!",
            full_name="Uploader Verify Impact", role="developer",
        )
        self.verifier = CustomUser.objects.create_user(
            email="verifier.verifyimpact@test.id", password="pass12345!",
            full_name="Verifier Verify Impact", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.uploader, role="owner", is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.verifier, role="member", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Verify Impact", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.req_status = ProjectRequirementStatus.objects.create(
            project=self.project,
            requirement=self.req,
            status=ProjectRequirementStatus.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def _upload_evidence(self):
        self._login_as(self.uploader)
        resp = self.client.post(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/evidence/",
            {"file_url": "https://example.com/kontrak.pdf"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        return self.req_status.evidence.filter(is_latest=True).first().id

    def test_approving_evidence_captures_nonzero_impact(self):
        """
        THE regression test. Approving evidence (the real cause &
        effect moment) must record a genuine, non-zero readiness/risk
        delta — not leave the fields None like before.
        """
        evidence_id = self._upload_evidence()

        self._login_as(self.verifier)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}"
            f"/evidence/{evidence_id}/verify/",
            {"action": "approve"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        latest_log = self.req_status.audit_logs.first()
        self.assertIsNotNone(latest_log.readiness_before)
        self.assertIsNotNone(latest_log.readiness_after)
        self.assertGreater(
            latest_log.readiness_after, latest_log.readiness_before,
            "Approving the only mandatory requirement should raise readiness"
        )

    def test_approving_evidence_patches_both_audit_logs(self):
        """
        approve() creates TWO audit logs (COMPLETED, then
        EVIDENCE_APPROVED) — both must carry the impact fields, not
        just whichever one happens to be 'latest'.
        """
        evidence_id = self._upload_evidence()

        self._login_as(self.verifier)
        self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}"
            f"/evidence/{evidence_id}/verify/",
            {"action": "approve"}, format="json",
        )

        recent_logs = list(self.req_status.audit_logs.order_by("-changed_at")[:2])
        actions = {log.action for log in recent_logs}
        self.assertIn("completed", actions)
        self.assertIn("evidence_approved", actions)
        for log in recent_logs:
            self.assertIsNotNone(
                log.readiness_before,
                f"'{log.action}' log must also carry impact data"
            )

    def test_activity_timeline_shows_delta_for_approval_event(self):
        """
        The real prod payoff: the Activity Timeline entry for the
        approval must carry a non-null, non-zero readiness_delta —
        this is what finally makes the badge appear on screen.
        """
        evidence_id = self._upload_evidence()

        self._login_as(self.verifier)
        self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}"
            f"/evidence/{evidence_id}/verify/",
            {"action": "approve"}, format="json",
        )

        resp = self.client.get(f"/api/projects/{self.project.id}/activity/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        latest = resp.data["results"][0]
        self.assertIn("readiness_delta", latest)
        self.assertIsNotNone(latest["readiness_delta"])
        self.assertNotEqual(
            latest["readiness_delta"], 0,
            "A completed mandatory requirement must show a real delta"
        )

    def test_rejecting_evidence_still_works_correctly(self):
        """
        Control case: rejection doesn't complete the requirement, so a
        zero delta here is CORRECT — guards against a future change
        accidentally treating rejection like completion.
        """
        evidence_id = self._upload_evidence()

        self._login_as(self.verifier)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}"
            f"/evidence/{evidence_id}/verify/",
            {"action": "reject", "notes": "Dokumen tidak lengkap"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req_status.refresh_from_db()
        self.assertEqual(self.req_status.status, ProjectRequirementStatus.Status.IN_PROGRESS)

    def test_uploader_still_cannot_verify_own_evidence(self):
        """Sanity check: this fix must not touch the self-verify guard."""
        evidence_id = self._upload_evidence()

        self._login_as(self.uploader)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}"
            f"/evidence/{evidence_id}/verify/",
            {"action": "approve"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["error_type"], "cannot_verify")


# =============================================================================
# Sprint 19 — Cross-project Calendar endpoint
# =============================================================================
class ProjectCalendarTests(APITestCase):
    """
    Sprint 19: standalone Calendar page backend. Cross-project view of
    every requirement with a due_date set, across the user's org only.
    No migration — due_date, is_overdue, days_until_due, and
    assigned_to have existed since Sprint 7.

    Covers:
    - Returns requirements with due dates, sorted chronologically
    - Excludes requirements without a due_date
    - Includes COMPLETED items too (frontend styles them, backend
      doesn't hide history)
    - is_overdue / days_until_due reflect the real Sprint 7 properties
    - assigned_to_name resolves correctly (or null when unassigned)
    - Tenant isolation: Org B never sees Org A's calendar items
    """

    def setUp(self):
        self.req1, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor Calendar", defaults={"is_mandatory": True, "weight": 60},
        )
        self.req2, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Rencana Kerja Calendar", defaults={"is_mandatory": True, "weight": 40},
        )
        self.req3, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.PERMITS,
            name="No Due Date Calendar", defaults={"is_mandatory": False, "weight": 10},
        )

        # ── Org A ─────────────────────────────────────────────
        self.org_a = Organization.objects.create(name="Asri Sentosa Calendar A")
        self.dev_a = CustomUser.objects.create_user(
            email="dev.calendar.a@test.id", password="pass12345!",
            full_name="Dev Calendar A", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.dev_a, role="owner", is_active=True,
        )
        self.project_a = Project.objects.create(
            organization=self.org_a, name="Cluster Calendar A", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )

        self.status_future = ProjectRequirementStatus.objects.create(
            project=self.project_a, requirement=self.req1,
            status=ProjectRequirementStatus.Status.IN_PROGRESS,
            due_date=date.today() + timedelta(days=5),
            assigned_to=self.dev_a,
        )
        self.status_overdue = ProjectRequirementStatus.objects.create(
            project=self.project_a, requirement=self.req2,
            status=ProjectRequirementStatus.Status.PENDING,
            due_date=date.today() - timedelta(days=3),
        )
        self.status_no_due = ProjectRequirementStatus.objects.create(
            project=self.project_a, requirement=self.req3,
            status=ProjectRequirementStatus.Status.PENDING,
        )

        # ── Org B — isolation control ───────────────────────────
        self.org_b = Organization.objects.create(name="Org B Calendar")
        self.dev_b = CustomUser.objects.create_user(
            email="dev.calendar.b@test.id", password="pass12345!",
            full_name="Dev Calendar B", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.dev_b, role="owner", is_active=True,
        )
        self.project_b = Project.objects.create(
            organization=self.org_b, name="Cluster Calendar B", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.status_b = ProjectRequirementStatus.objects.create(
            project=self.project_b, requirement=self.req1,
            status=ProjectRequirementStatus.Status.PENDING,
            due_date=date.today() + timedelta(days=2),
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_returns_only_requirements_with_due_date(self):
        self._login_as(self.dev_a)
        resp = self.client.get("/api/projects/calendar/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in resp.data["results"]}
        self.assertIn(str(self.status_future.id), ids)
        self.assertIn(str(self.status_overdue.id), ids)
        self.assertNotIn(str(self.status_no_due.id), ids)

    def test_sorted_chronologically(self):
        self._login_as(self.dev_a)
        resp = self.client.get("/api/projects/calendar/")
        due_dates = [item["due_date"] for item in resp.data["results"]]
        self.assertEqual(due_dates, sorted(due_dates))

    def test_overdue_flagged_correctly(self):
        self._login_as(self.dev_a)
        resp = self.client.get("/api/projects/calendar/")
        overdue_item = next(i for i in resp.data["results"] if i["id"] == str(self.status_overdue.id))
        future_item  = next(i for i in resp.data["results"] if i["id"] == str(self.status_future.id))
        self.assertTrue(overdue_item["is_overdue"])
        self.assertFalse(future_item["is_overdue"])
        self.assertLess(overdue_item["days_until_due"], 0)
        self.assertGreater(future_item["days_until_due"], 0)

    def test_includes_assigned_to_name(self):
        self._login_as(self.dev_a)
        resp = self.client.get("/api/projects/calendar/")
        assigned_item = next(i for i in resp.data["results"] if i["id"] == str(self.status_future.id))
        self.assertEqual(assigned_item["assigned_to_name"], "Dev Calendar A")
        unassigned_item = next(i for i in resp.data["results"] if i["id"] == str(self.status_overdue.id))
        self.assertIsNone(unassigned_item["assigned_to_name"])

    def test_completed_requirement_still_shown_but_not_overdue(self):
        """
        A completed requirement with a due date should still appear —
        the frontend can style it (e.g. greyed out), but the backend
        shouldn't silently erase it from history.
        """
        self.status_overdue.status = ProjectRequirementStatus.Status.COMPLETED
        self.status_overdue.save(update_fields=["status"])

        self._login_as(self.dev_a)
        resp = self.client.get("/api/projects/calendar/")
        ids = {item["id"] for item in resp.data["results"]}
        self.assertIn(str(self.status_overdue.id), ids)

        item = next(i for i in resp.data["results"] if i["id"] == str(self.status_overdue.id))
        self.assertFalse(item["is_overdue"], "Completed items are never overdue")

    def test_tenant_isolation_org_a_cannot_see_org_b(self):
        """Org A's calendar must never include Org B's requirements."""
        self._login_as(self.dev_a)
        resp = self.client.get("/api/projects/calendar/")
        ids = {item["id"] for item in resp.data["results"]}
        self.assertNotIn(str(self.status_b.id), ids)

    def test_tenant_isolation_org_b_sees_only_its_own(self):
        self._login_as(self.dev_b)
        resp = self.client.get("/api/projects/calendar/")
        ids = {item["id"] for item in resp.data["results"]}
        self.assertEqual(ids, {str(self.status_b.id)})


# =============================================================================
# Sprint 20 — Readiness Momentum + Decision Engine Feedback Loop (backend)
# =============================================================================
class RequirementUpdateFeedbackLoopTests(APITestCase):
    """
    Sprint 20: the "dopamine sprint" backend. Most of the underlying
    delta capture (readiness/risk before/after, stage_can_advance)
    already existed since the Sprint 16 bug hunt — this adds the two
    genuinely new pieces the roadmap actually asked for: newly_unlocked
    and a dynamic, impact-aware celebratory message.

    Covers:
    - Completing a requirement that unblocks a real downstream
      dependent lists it in newly_unlocked
    - Completing a requirement with no dependents leaves it empty
    - Celebratory message fires (name + unlocked + stage-ready) when
      completing the last blocker
    - Non-completing status changes keep the message generic — no
      false celebration
    """

    def setUp(self):
        self.req_first, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Rencana Kerja Feedback", defaults={"is_mandatory": True, "weight": 100},
        )
        self.req_second, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor Feedback", defaults={"is_mandatory": True, "weight": 0},
        )
        self.req_second.prerequisites.add(self.req_first)

        self.req_isolated, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Isolated Feedback", defaults={"is_mandatory": True, "weight": 0},
        )

        self.org = Organization.objects.create(name="Asri Sentosa Feedback")
        self.dev = CustomUser.objects.create_user(
            email="dev.feedback@test.id", password="pass12345!",
            full_name="Dev Feedback", role="developer",
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.dev, role="owner", is_active=True,
        )
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Feedback", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.status_first = ProjectRequirementStatus.objects.create(
            project=self.project, requirement=self.req_first,
            status=ProjectRequirementStatus.Status.PENDING,
        )
        self.status_second = ProjectRequirementStatus.objects.create(
            project=self.project, requirement=self.req_second,
            status=ProjectRequirementStatus.Status.PENDING,
        )
        self.status_isolated = ProjectRequirementStatus.objects.create(
            project=self.project, requirement=self.req_isolated,
            status=ProjectRequirementStatus.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_newly_unlocked_lists_the_downstream_requirement(self):
        """Completing the prerequisite unlocks its real dependent."""
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.status_first.id}/",
            {"status": "completed"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("Kontraktor Feedback", resp.data["impact"]["newly_unlocked"])

    def test_newly_unlocked_empty_when_nothing_downstream(self):
        """Completing a requirement with no dependents unlocks nothing."""
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.status_isolated.id}/",
            {"status": "completed"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["impact"]["newly_unlocked"], [])

    def test_celebratory_message_when_stage_can_advance(self):
        """
        Completing the only remaining blocker produces the full
        celebratory sentence: name + unlocked + stage-ready — exactly
        the "Kontraktor selesai! ... Tahap siap dilanjutkan. 🎉" shape
        from the roadmap spec.
        """
        self.status_first.mark_completed(user=self.dev)
        self.status_isolated.mark_completed(user=self.dev)

        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.status_second.id}/",
            {"status": "completed"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg = resp.data["impact"]["message"]
        self.assertIn("Kontraktor Feedback selesai!", msg)
        self.assertIn("Tahap siap dilanjutkan", msg)

    def test_generic_message_for_non_completing_status_change(self):
        """
        Marking something in_progress (not completed) keeps the
        message generic — no false celebration, no phantom unlocks.
        """
        self._login_as(self.dev)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.status_first.id}/",
            {"status": "in_progress"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotIn("selesai", resp.data["impact"]["message"])
        self.assertEqual(resp.data["impact"]["newly_unlocked"], [])


class EvidenceEndpointsImpactSchemaTests(APITestCase):
    """
    Sprint 20: evidence upload + verify endpoints now also return
    'impact' with the same shape as ProjectRequirementUpdateView.
    Previously both endpoints captured readiness/risk deltas
    internally (Sprint 16 fix) but never surfaced them in the API
    response — meaning the Sprint 20 frontend feedback loop would've
    stayed completely silent for the two actions people actually use
    every day (upload evidence, approve/reject evidence), only ever
    firing for the rarely-used direct status-update endpoint.
    """

    def setUp(self):
        self.req, _ = StageRequirement.objects.get_or_create(
            stage=StageRequirement.Stage.CONSTRUCTION,
            name="Kontraktor Impact Schema", defaults={"is_mandatory": True, "weight": 60},
        )
        self.org = Organization.objects.create(name="Asri Sentosa Impact Schema")
        self.uploader = CustomUser.objects.create_user(
            email="uploader.impactschema@test.id", password="pass12345!",
            full_name="Uploader Impact Schema", role="developer",
        )
        self.verifier = CustomUser.objects.create_user(
            email="verifier.impactschema@test.id", password="pass12345!",
            full_name="Verifier Impact Schema", role="developer",
        )
        OrganizationMembership.objects.create(organization=self.org, user=self.uploader, role="owner", is_active=True)
        OrganizationMembership.objects.create(organization=self.org, user=self.verifier, role="member", is_active=True)
        self.project = Project.objects.create(
            organization=self.org, name="Cluster Impact Schema", location="Jambi",
            stage=Project.Stage.CONSTRUCTION,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        self.req_status = ProjectRequirementStatus.objects.create(
            project=self.project, requirement=self.req,
            status=ProjectRequirementStatus.Status.PENDING,
        )

    def _login_as(self, user):
        self.client.force_authenticate(user=user)

    def test_evidence_upload_response_includes_impact(self):
        self._login_as(self.uploader)
        resp = self.client.post(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/evidence/",
            {"file_url": "https://example.com/kontrak.pdf"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("impact", resp.data)
        self.assertIn("readiness_delta", resp.data["impact"])
        self.assertIn("newly_unlocked", resp.data["impact"])
        self.assertEqual(resp.data["impact"]["newly_unlocked"], [])

    def test_evidence_approval_response_includes_impact_with_real_delta(self):
        self._login_as(self.uploader)
        self.client.post(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/evidence/",
            {"file_url": "https://example.com/kontrak.pdf"}, format="json",
        )
        evidence_id = self.req_status.evidence.filter(is_latest=True).first().id

        self._login_as(self.verifier)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}"
            f"/evidence/{evidence_id}/verify/",
            {"action": "approve"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("impact", resp.data)
        self.assertGreater(resp.data["impact"]["readiness_delta"], 0)
        self.assertIn("selesai!", resp.data["impact"]["message"])

    def test_evidence_rejection_response_includes_impact_with_zero_delta(self):
        self._login_as(self.uploader)
        self.client.post(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}/evidence/",
            {"file_url": "https://example.com/kontrak.pdf"}, format="json",
        )
        evidence_id = self.req_status.evidence.filter(is_latest=True).first().id

        self._login_as(self.verifier)
        resp = self.client.put(
            f"/api/projects/{self.project.id}/requirements/{self.req_status.id}"
            f"/evidence/{evidence_id}/verify/",
            {"action": "reject", "notes": "kurang jelas"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("impact", resp.data)
        self.assertEqual(resp.data["impact"]["readiness_delta"], 0)
        self.assertEqual(resp.data["impact"]["newly_unlocked"], [])
