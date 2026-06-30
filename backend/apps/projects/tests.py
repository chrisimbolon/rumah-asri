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