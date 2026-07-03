# ======================================================
# === backend/apps/assistant/urls.py ===
# Sprint 15: Business Assistant URL patterns.
# Mounted at /api/assistant/ in config/urls.py
# ======================================================
from django.urls import path

from .views import AssistantQueryView

urlpatterns = [
    # POST /api/assistant/query/
    path("query/", AssistantQueryView.as_view(), name="assistant-query"),
]
