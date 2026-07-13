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

from .models import Prospect
from .serializers import ProspectCreateSerializer, ProspectSerializer


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
