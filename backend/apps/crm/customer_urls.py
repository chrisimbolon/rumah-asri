# =============================================================================
# === backend/apps/crm/customer_urls.py ===
# Sprint 8 (CRM Foundation Phase B): /api/customers/
#
# Deliberately a separate urls module from crm/urls.py — that one is
# mounted at /api/prospects/ in config/urls.py (Sprint 2.5), so adding
# a bare path("") here would collide with ProspectListView. Customer
# is its own top-level resource, not nested under Prospect.
# =============================================================================
from django.urls import path

from .views import CustomerProfileDetailView, CustomerProfileListView

urlpatterns = [
    path("",
         CustomerProfileListView.as_view(),
         name="customer-list"),

    path("<uuid:pk>/",
         CustomerProfileDetailView.as_view(),
         name="customer-detail"),
]
