# =============================================================================
# === backend/config/urls.py ===
# =============================================================================
"""
DevelopIndo — Root URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # ── Django admin ──────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Auth ──────────────────────────────────────────────────
    path("api/auth/",          include("apps.authentication.urls")),

    # ── Organizations (super admin + my org) ──────────────────
    path("api/organizations/", include("apps.organizations.urls")),

    # ── Core resources ────────────────────────────────────────
    path("api/projects/",      include("apps.projects.urls")),
    path("api/units/",         include("apps.units.urls")),
    path("api/construction/",  include("apps.construction.urls")),
    path("api/payments/",      include("apps.payments.urls")),
    path("api/documents/",     include("apps.documents.urls")),

    # ── Buyer portal ──────────────────────────────────────────
    path("api/buyer/",         include("apps.buyer.urls")),
]

# ── Serve media files in development ─────────────────────────
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
