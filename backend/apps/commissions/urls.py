# =============================================================================
# === backend/apps/commissions/urls.py ===
# =============================================================================
from django.urls import path

from .views import CommissionDetailView, CommissionListView, CommissionPolicyView

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

    path("<uuid:pk>/",
         CommissionDetailView.as_view(),
         name="commission-detail"),
]
