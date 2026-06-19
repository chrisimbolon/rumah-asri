# =============================================================================
# === backend/apps/organizations/urls.py ===
# =============================================================================
"""
RumahAsri — Organizations URLs
"""
from django.urls import path
from .views import MyOrganizationView, OrganizationDetailView, OrganizationListView

urlpatterns = [
    path("",         OrganizationListView.as_view(),  name="organization-list"),
    path("mine/",    MyOrganizationView.as_view(),    name="organization-mine"),
    path("<uuid:pk>/", OrganizationDetailView.as_view(), name="organization-detail"),
]
