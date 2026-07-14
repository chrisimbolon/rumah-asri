# =============================================================================
# === backend/apps/crm/views.py ===
# CRM Foundation Sprint 2.5: Prospect CRUD.
#
# Endpoints:
#   GET  /api/prospects/       ← list prospects for org, filterable
#   POST /api/prospects/       ← create new prospect
#   GET  /api/prospects/<id>/  ← get single prospect
#   PUT  /api/prospects/<id>/  ← update prospect (status, follow-up, etc)
#
# No DELETE — a lost lead is `status=hilang`, not a deleted row. Same
# "audit trail over hard delete" instinct the rest of this codebase
# already follows (see UnitPriceHistory, RequirementAudit, FinancialAudit).
# =============================================================================
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import Activity, Prospect, SiteVisit
from .serializers import ActivitySerializer, ProspectCreateSerializer, ProspectSerializer, SiteVisitSerializer


class ProspectListView(TenantScopedAPIView):
    model = Prospect

    def get(self, request):
        prospects = self.get_queryset()

        status_filter = request.query_params.get("status")
        project_id    = request.query_params.get("project")

        if status_filter:
            prospects = prospects.filter(status=status_filter)
        if project_id:
            prospects = prospects.filter(interested_project__id=project_id)

        serializer = ProspectSerializer(prospects, many=True)
        return Response({
            "success": True,
            "count":   prospects.count(),
            "results": serializer.data,
        })

    def post(self, request):
        if request.user.role not in ("developer", "agent", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ProspectCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            prospect = serializer.save()
            return Response({
                "success": True,
                "message":  f"Prospect {prospect.name} berhasil dibuat",
                "prospect": ProspectSerializer(prospect).data,
            }, status=status.HTTP_201_CREATED)
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProspectDetailView(TenantScopedAPIView):
    model = Prospect

    def get(self, request, pk):
        prospect = self.get_object(pk)
        return Response({"success": True, "prospect": ProspectSerializer(prospect).data})

    def put(self, request, pk):
        # Deliberately stricter than UnitDetailView.put() (which has no
        # role gate at all) — new code doesn't need to inherit that gap
        # just for consistency's sake.
        if request.user.role not in ("developer", "agent", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        prospect = self.get_object(pk)
        serializer = ProspectCreateSerializer(
            prospect, data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message":  f"Prospect {prospect.name} berhasil diperbarui",
                "prospect": ProspectSerializer(prospect).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ActivityListView(TenantScopedAPIView):
    """
    GET  /api/prospects/<prospect_id>/activities/
    POST /api/prospects/<prospect_id>/activities/

    Sprint 4 (CRM Foundation Phase B): follow-up history for a single
    Prospect. Deliberately scoped through `Prospect`'s own tenant check
    rather than giving `Activity` a separate detail endpoint — the URL
    always names a prospect_id, and self.get_object() (inherited from
    TenantScopedAPIView, model=Prospect) 404s on a cross-org prospect
    before a single Activity row is ever queried. No separate tenant
    check needed on Activity itself; access is fully gated by its
    parent.
    """
    model = Prospect

    def get(self, request, prospect_id):
        prospect = self.get_object(prospect_id)
        activities = prospect.activities.all()
        serializer = ActivitySerializer(activities, many=True)
        return Response({
            "success": True,
            "count":   activities.count(),
            "results": serializer.data,
        })

    def post(self, request, prospect_id):
        if request.user.role not in ("developer", "agent", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        prospect = self.get_object(prospect_id)
        serializer = ActivitySerializer(data=request.data)
        if serializer.is_valid():
            activity = serializer.save(
                prospect=prospect,
                organization=prospect.organization,
                created_by=request.user,
            )
            return Response({
                "success":  True,
                "message":  "Aktivitas berhasil dicatat",
                "activity": ActivitySerializer(activity).data,
            }, status=status.HTTP_201_CREATED)
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SiteVisitListView(TenantScopedAPIView):
    """
    GET  /api/prospects/<prospect_id>/site-visits/
    POST /api/prospects/<prospect_id>/site-visits/

    Sprint 6 (CRM Foundation Phase B). Same nested-under-Prospect
    tenant-scoping pattern ActivityListView (Sprint 4) already
    established — access is fully gated by resolving the parent
    Prospect first via self.get_object(), no separate tenant check
    needed on SiteVisit itself.
    """
    model = Prospect

    def get(self, request, prospect_id):
        prospect = self.get_object(prospect_id)
        visits = prospect.site_visits.all()
        serializer = SiteVisitSerializer(visits, many=True)
        return Response({
            "success": True,
            "count":   visits.count(),
            "results": serializer.data,
        })

    def post(self, request, prospect_id):
        if request.user.role not in ("developer", "agent", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        prospect = self.get_object(prospect_id)
        serializer = SiteVisitSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            visit = serializer.save(
                prospect=prospect,
                organization=prospect.organization,
                created_by=request.user,
            )
            return Response({
                "success":     True,
                "message":     "Kunjungan berhasil dijadwalkan",
                "site_visit":  SiteVisitSerializer(visit).data,
            }, status=status.HTTP_201_CREATED)
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SiteVisitDetailView(TenantScopedAPIView):
    """
    PUT /api/prospects/<prospect_id>/site-visits/<visit_id>/

    Sprint 6: status updates (completed/no_show/cancelled) and
    reschedules. Scoped through Prospect first (tenant check), then
    the specific SiteVisit is looked up filtered by that exact
    prospect — a visit_id belonging to a DIFFERENT prospect in the
    SAME org still 404s here, not just cross-org ones.
    """
    model = Prospect

    def put(self, request, prospect_id, visit_id):
        if request.user.role not in ("developer", "agent", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        prospect = self.get_object(prospect_id)
        try:
            visit = prospect.site_visits.get(id=visit_id)
        except SiteVisit.DoesNotExist:
            return Response(
                {"success": False, "message": "Kunjungan tidak ditemukan."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SiteVisitSerializer(
            visit, data=request.data, partial=True, context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success":    True,
                "message":    "Kunjungan berhasil diperbarui",
                "site_visit": SiteVisitSerializer(visit).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
