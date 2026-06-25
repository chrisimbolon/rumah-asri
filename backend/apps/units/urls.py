# =============================================================================
# === backend/apps/units/urls.py ===
# =============================================================================
"""
DevelopIndo — Units URLs
"""
from django.urls import path

from .views import (
    BookingCancelView,
    UnitBookingView,
    UnitDetailView,
    UnitListView,
)

urlpatterns = [
    path("",
         UnitListView.as_view(),
         name="unit-list"),

    path("<uuid:pk>/",
         UnitDetailView.as_view(),
         name="unit-detail"),

    path("<uuid:pk>/book/",
         UnitBookingView.as_view(),
         name="unit-book"),

    path("bookings/<uuid:booking_id>/cancel/",
         BookingCancelView.as_view(),
         name="booking-cancel"),
]
