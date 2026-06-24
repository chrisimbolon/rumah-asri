# =============================================================================
# === backend/apps/projects/urls.py ===
# =============================================================================
"""
DevelopIndo — Projects URLs
"""
from django.urls import path

from .views import (
    ProjectAdvanceView,
    ProjectDetailView,
    ProjectIntelligenceView,
    ProjectListView,
    ProjectPortfolioView,
    ProjectRequirementUpdateView,
)

urlpatterns = [
    # Portfolio overview — must be before <uuid:pk> to avoid conflict
    path("portfolio/",
         ProjectPortfolioView.as_view(),
         name="project-portfolio"),

    # List + create
    path("",
         ProjectListView.as_view(),
         name="project-list"),

    # Detail + update + delete
    path("<uuid:pk>/",
         ProjectDetailView.as_view(),
         name="project-detail"),

    # Lifecycle advancement
    path("<uuid:pk>/advance/",
         ProjectAdvanceView.as_view(),
         name="project-advance"),

    # Intelligence summary
    path("<uuid:pk>/intelligence/",
         ProjectIntelligenceView.as_view(),
         name="project-intelligence"),

    # Update single requirement status
    path("<uuid:pk>/requirements/<uuid:req_status_id>/",
         ProjectRequirementUpdateView.as_view(),
         name="project-requirement-update"),
]
