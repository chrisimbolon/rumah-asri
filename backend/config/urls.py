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
from django.http import JsonResponse


urlpatterns = [
    # ── Django admin ──────────────────────────────────────────
    path("admin/", admin.site.urls),

    path("api/health/", lambda r: JsonResponse({"status": "ok", "service": "developindo"})),

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
    path("api/prospects/",     include("apps.crm.urls")),
    # Sprint 8 (CRM Foundation Phase B): separate module, not nested
    # under prospects — see apps/crm/customer_urls.py's own docstring.
    path("api/customers/",     include("apps.crm.customer_urls")),

    # ── Buyer portal ──────────────────────────────────────────
    path("api/buyer/",         include("apps.buyer.urls")),
]

# ── Serve media files in development ─────────────────────────
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
