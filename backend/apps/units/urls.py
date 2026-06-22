"""
DevelopIndo — Units URLs
"""

from django.urls import path

from .views import UnitDetailView, UnitListView

urlpatterns = [
    path("",           UnitListView.as_view(),   name="unit-list"),
    path("<uuid:pk>/", UnitDetailView.as_view(), name="unit-detail"),
]