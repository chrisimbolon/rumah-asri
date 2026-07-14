# =============================================================================
# === backend/apps/crm/urls.py ===
# =============================================================================
"""
DevelopIndo — CRM (Prospect) URLs
"""
from django.urls import path

from .views import (
    ActivityListView,
    ProspectDetailView,
    ProspectListView,
    SiteVisitDetailView,
    SiteVisitListView,
)

urlpatterns = [
    path("",
         ProspectListView.as_view(),
         name="prospect-list"),

    path("<uuid:pk>/",
         ProspectDetailView.as_view(),
         name="prospect-detail"),

    # Sprint 4 (CRM Foundation Phase B)
    path("<uuid:prospect_id>/activities/",
         ActivityListView.as_view(),
         name="prospect-activities"),

    # Sprint 6 (CRM Foundation Phase B)
    path("<uuid:prospect_id>/site-visits/",
         SiteVisitListView.as_view(),
         name="prospect-site-visits"),

    path("<uuid:prospect_id>/site-visits/<uuid:visit_id>/",
         SiteVisitDetailView.as_view(),
         name="prospect-site-visit-detail"),
]
