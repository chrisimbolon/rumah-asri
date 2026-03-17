"""
RumahAsri — Buyer Portal URLs
Mounted at /api/buyer/ in config/urls.py

All routes:
  GET /api/buyer/me/          ← unit + buyer info
  GET /api/buyer/timeline/    ← construction phases
  GET /api/buyer/payments/    ← payment schedule
  GET /api/buyer/documents/   ← documents
"""

from django.urls import path
from .views import (
    BuyerMeView,
    BuyerTimelineView,
    BuyerPaymentsView,
    BuyerDocumentsView,
)

urlpatterns = [
    path("me/",        BuyerMeView.as_view(),        name="buyer-me"),
    path("timeline/",  BuyerTimelineView.as_view(),  name="buyer-timeline"),
    path("payments/",  BuyerPaymentsView.as_view(),  name="buyer-payments"),
    path("documents/", BuyerDocumentsView.as_view(), name="buyer-documents"),
]
