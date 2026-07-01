# =============================================================================
# backend/apps/projects/urls.py
# Sprint 10: adds readiness-history/ endpoint.
# All Sprint 1-9 URLs preserved — additive only.
# =============================================================================
from django.urls import path

from .views import (
    AssignRequirementView,
    EvidenceEligibleVerifiersView,
    MyActionsView,
    ProjectActivityView,
    ProjectAdvanceView,
    ProjectDetailView,
    ProjectFinancialView,
    ProjectIntelligenceView,
    ProjectListView,
    ProjectOrgMembersView,
    ProjectPortfolioView,
    ProjectReadinessHistoryView,        # Sprint 10
    ProjectRequirementUpdateView,
    RequirementCommentView,
    RequirementEvidenceVerifyView,
    RequirementEvidenceView,
)

urlpatterns = [
    # ── Portfolio overview ─────────────────────────────────────
    path("portfolio/",
         ProjectPortfolioView.as_view(),
         name="project-portfolio"),

    path("my-actions/",
         MyActionsView.as_view(),
         name="project-my-actions"),

    # ── List + create ──────────────────────────────────────────
    path("",
         ProjectListView.as_view(),
         name="project-list"),

    # ── Detail + update + delete ───────────────────────────────
    path("<uuid:pk>/",
         ProjectDetailView.as_view(),
         name="project-detail"),

    # ── Lifecycle advancement ──────────────────────────────────
    path("<uuid:pk>/advance/",
         ProjectAdvanceView.as_view(),
         name="project-advance"),

    # ── Intelligence summary ───────────────────────────────────
    path("<uuid:pk>/intelligence/",
         ProjectIntelligenceView.as_view(),
         name="project-intelligence"),

    # ── Sprint 10: Readiness trend history ────────────────────
    path("<uuid:pk>/readiness-history/",
         ProjectReadinessHistoryView.as_view(),
         name="project-readiness-history"),

    # ── Update single requirement status ──────────────────────
    path("<uuid:pk>/requirements/<uuid:req_status_id>/",
         ProjectRequirementUpdateView.as_view(),
         name="project-requirement-update"),

    # ── Evidence upload + list ─────────────────────────────────
    path("<uuid:pk>/requirements/<uuid:req_status_id>/evidence/",
         RequirementEvidenceView.as_view(),
         name="project-requirement-evidence"),

    # ── Evidence verify (approve/reject) ──────────────────────
    path("<uuid:pk>/requirements/<uuid:req_status_id>/evidence/<uuid:ev_id>/verify/",
         RequirementEvidenceVerifyView.as_view(),
         name="project-requirement-evidence-verify"),

    # ── Evidence eligible verifiers ───────────────────────────
    path("<uuid:pk>/requirements/<uuid:req_status_id>/evidence/<uuid:ev_id>/verifiers/",
         EvidenceEligibleVerifiersView.as_view(),
         name="evidence-eligible-verifiers"),

    # ── Sprint 3: Activity timeline ────────────────────────────
    path("<uuid:pk>/activity/",
         ProjectActivityView.as_view(),
         name="project-activity"),

    # ── Sprint 3: Financial snapshot ──────────────────────────
    path("<uuid:pk>/financial/",
         ProjectFinancialView.as_view(),
         name="project-financial"),

    # ── Sprint 7: Assign + due date ───────────────────────────
    path("<uuid:pk>/requirements/<uuid:req_status_id>/assign/",
         AssignRequirementView.as_view(),
         name="requirement-assign"),

    # ── Sprint 7: Comments ────────────────────────────────────
    path("<uuid:pk>/requirements/<uuid:req_status_id>/comments/",
         RequirementCommentView.as_view(),
         name="requirement-comments"),

    # ── Sprint 7: Org members ─────────────────────────────────
    path("<uuid:pk>/members/",
         ProjectOrgMembersView.as_view(),
         name="project-members"),
]
