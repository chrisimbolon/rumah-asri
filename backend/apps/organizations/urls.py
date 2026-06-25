# =============================================================================
# === backend/apps/organizations/urls.py ===
# =============================================================================
"""
DevelopIndo — Organizations URLs
"""
from django.urls import path
from .views import BuyerListView, MyOrganizationView, OrganizationDetailView, OrganizationListView

urlpatterns = [
    path("",         OrganizationListView.as_view(),  name="organization-list"),
    path("mine/",    MyOrganizationView.as_view(),    name="organization-mine"),
    path("buyers/",    BuyerListView.as_view(),         name="buyer-list"),
    path("<uuid:pk>/", OrganizationDetailView.as_view(), name="organization-detail"),
]
