"""
RumahAsri — Construction URLs
"""

from django.urls import path

from .views import PhaseDetailView, PhaseListView, PhasePhotoView

urlpatterns = [
    path("<uuid:unit_id>/phases/",              PhaseListView.as_view(),   name="phase-list"),
    path("phases/<uuid:phase_id>/",             PhaseDetailView.as_view(), name="phase-detail"),
    path("phases/<uuid:phase_id>/photos/",      PhasePhotoView.as_view(),  name="phase-photos"),
]