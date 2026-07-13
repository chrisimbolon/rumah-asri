# =============================================================================
# === backend/apps/crm/urls.py ===
# =============================================================================
"""
DevelopIndo — CRM (Prospect) URLs
"""
from django.urls import path

from .views import ProspectDetailView, ProspectListView

urlpatterns = [
    path("",
         ProspectListView.as_view(),
         name="prospect-list"),

    path("<uuid:pk>/",
         ProspectDetailView.as_view(),
         name="prospect-detail"),
]
