"""
DevelopIndo — Payments URLs
"""

from django.urls import path

from .views import FinancialAuditListView, PaymentDetailView, PaymentListView

urlpatterns = [
    path("",           PaymentListView.as_view(),      name="payment-list"),
    path("<uuid:pk>/", PaymentDetailView.as_view(),     name="payment-detail"),
    # Sprint 27: placed before the "audit" could ever collide with the
    # <uuid:pk> pattern above — "audit" isn't a valid UUID, so Django's
    # URL resolver would never actually mismatch here, but ordering it
    # first keeps the intent obvious at a glance.
    path("audit/",     FinancialAuditListView.as_view(), name="financial-audit-list"),
]