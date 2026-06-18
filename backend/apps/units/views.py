# =============================================================================
# === apps/units/views.py ===
# =============================================================================
"""
RumahAsri — Units Views (developer/agent dashboard side)

NOTE — behaviour change: the old buyer-branch in UnitListView has been
removed. Buyers should exclusively use /api/buyer/* (apps/buyer/views.py),
which already scopes correctly via `Unit.objects.get(buyer=user)` and is
untouched by this change. If anything on the frontend still calls
/api/units/ as a buyer, it will now get an empty result set (buyers have
no OrganizationMembership) rather than their own unit — point it at
/api/buyer/me/ instead.
"""
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import Unit
from .serializers import UnitCreateSerializer, UnitSerializer


class UnitListView(TenantScopedAPIView):
    model = Unit

    def get(self, request):
        units = self.get_queryset()

        project_id = request.query_params.get("project")
        if project_id:
            units = units.filter(project__id=project_id)

        unit_status = request.query_params.get("status")
        if unit_status:
            units = units.filter(status=unit_status)

        serializer = UnitSerializer(units, many=True)
        return Response({
            "success": True,
            "count":   units.count(),
            "results": serializer.data,
        })

    def post(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = UnitCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            unit = serializer.save()
            return Response({
                "success": True,
                "message": f"Unit {unit.unit_number} berhasil dibuat",
                "unit":    UnitSerializer(unit).data,
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UnitDetailView(TenantScopedAPIView):
    """
    THE FIX: no more role branching to forget. Every role (developer,
    agent, super_admin) is scoped identically through
    Unit.objects.for_user() — there's no longer a code path where an
    unhandled role falls through to unrestricted access.
    """
    model = Unit

    def get(self, request, pk):
        unit = self.get_object(pk)
        return Response({"success": True, "unit": UnitSerializer(unit).data})

    def put(self, request, pk):
        unit = self.get_object(pk)
        serializer = UnitCreateSerializer(
            unit, data=request.data, partial=True, context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": f"Unit {unit.unit_number} berhasil diperbarui",
                "unit":    UnitSerializer(unit).data,
            })
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)