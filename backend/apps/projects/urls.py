# =============================================================================
# === backend/apps/projects/urls.py ===
# =============================================================================
"""
DevelopIndo — Projects URLs
"""
from django.urls import path

from .views import ProjectAdvanceView, ProjectDetailView, ProjectListView

urlpatterns = [
    path("",                    ProjectListView.as_view(),   name="project-list"),
    path("<uuid:pk>/",          ProjectDetailView.as_view(), name="project-detail"),
    path("<uuid:pk>/advance/",  ProjectAdvanceView.as_view(), name="project-advance"),
]
