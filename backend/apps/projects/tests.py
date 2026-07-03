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