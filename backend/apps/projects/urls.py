# =============================================================================
# backend/apps/projects/urls.py
# Sprint 18: adds /portfolio-intelligence/ endpoint.
# All Sprint 1-17 URLs preserved — additive only.
# =============================================================================
from django.urls import path

from .views import (
    AssignRequirementView,
    EvidenceEligibleVerifiersView,
    MyActionsView,
    PortfolioIntelligenceView,          # Sprint 18
    ProjectActivityView,
    ProjectAdvanceView,
    ProjectDecisionEngineView,
    ProjectDependencyGraphView,
    ProjectDetailView,
    ProjectFinancialView,
    ProjectIntelligenceView,
    ProjectListView,
    ProjectOrgMembersView,
    ProjectPortfolioView,
    ProjectReadinessHistoryView,
    ProjectRecentActivityView,
    ProjectRequirementUpdateView,
    ProjectRiskForecastView,
    ProjectPulseView,
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

    # ── Sprint 17: Cross-project recent activity ───────────────
    path("recent-activity/",
         ProjectRecentActivityView.as_view(),
         name="project-recent-activity"),

    # ── Sprint 18: Portfolio Intelligence Hub ─────────────────
    path("portfolio-intelligence/",
         PortfolioIntelligenceView.as_view(),
         name="project-portfolio-intelligence"),

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

    # ── Sprint 11: Dependency graph ───────────────────────────
    path("<uuid:pk>/dependency-graph/",
         ProjectDependencyGraphView.as_view(),
         name="project-dependency-graph"),

    # ── Sprint 13: Decision Engine ────────────────────────────
    path("<uuid:pk>/decision/",
         ProjectDecisionEngineView.as_view(),
         name="project-decision-engine"),

    # ── Sprint 14: Risk Forecast ──────────────────────────────
    path("<uuid:pk>/risk-forecast/",
         ProjectRiskForecastView.as_view(),
         name="project-risk-forecast"),

    # ── Sprint 17: Live pulse ─────────────────────────────────
    path("<uuid:pk>/pulse/",
         ProjectPulseView.as_view(),
         name="project-pulse"),

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
