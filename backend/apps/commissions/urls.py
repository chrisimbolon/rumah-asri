# =============================================================================
# === backend/apps/commissions/urls.py ===
# =============================================================================
from django.urls import path

from .views import (
    CommissionDetailView,
    CommissionListView,
    CommissionPolicyView,
    CommissionTierDetailView,
    CommissionTierListView,
)

urlpatterns = [
    path("",
         CommissionListView.as_view(),
         name="commission-list"),

    # Placed before <uuid:pk>/ for readability — Django's uuid
    # converter validates format, so "policy" could never actually
    # match it, but this ordering keeps the file honest to read.
    path("policy/",
         CommissionPolicyView.as_view(),
         name="commission-policy"),

    # Sprint 2 (Commission Foundation)
    path("policy/tiers/",
         CommissionTierListView.as_view(),
         name="commission-tier-list"),

    path("policy/tiers/<uuid:pk>/",
         CommissionTierDetailView.as_view(),
         name="commission-tier-detail"),

    path("<uuid:pk>/",
         CommissionDetailView.as_view(),
         name="commission-detail"),
]
