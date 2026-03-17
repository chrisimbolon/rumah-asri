"""
RumahAsri — Payments URLs
"""

from django.urls import path

from .views import PaymentDetailView, PaymentListView

urlpatterns = [
    path("",           PaymentListView.as_view(),   name="payment-list"),
    path("<uuid:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
]