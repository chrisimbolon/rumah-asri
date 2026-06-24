# =============================================================================
# === backend/apps/organizations/views.py ===
# =============================================================================
"""
DevelopIndo — Organizations Views

Endpoints:
  GET /api/organizations/         ← super_admin: all orgs | developer/agent: own org
  GET /api/organizations/mine/    ← current user's organization (any authenticated role)
  GET /api/organizations/<id>/    ← org detail with memberships (super_admin only)
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Organization, OrganizationMembership
from .serializers import OrganizationDetailSerializer, OrganizationSerializer


class OrganizationListView(APIView):
    """
    GET /api/organizations/
    super_admin  → all organizations on the platform
    developer    → only their own organization
    agent        → only their organization
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == "super_admin":
            orgs = Organization.objects.all().order_by("name")
        else:
            org_ids = request.user.memberships.filter(
                is_active=True
            ).values_list("organization_id", flat=True)
            orgs = Organization.objects.filter(id__in=org_ids)

        serializer = OrganizationSerializer(orgs, many=True)
        return Response({
            "success": True,
            "count":   orgs.count(),
            "results": serializer.data,
        })


class MyOrganizationView(APIView):
    """
    GET /api/organizations/mine/
    Returns the current user's primary organization.
    Used by the Sidebar to show a real org name instead of mock data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = request.user.memberships.filter(
            is_active=True
        ).select_related("organization").first()

        if not membership:
            return Response(
                {
                    "success": False,
                    "message": "Anda belum tergabung dalam organisasi manapun.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OrganizationSerializer(membership.organization)
        return Response({
            "success":      True,
            "organization": serializer.data,
            "role":         membership.role,
        })


class OrganizationDetailView(APIView):
    """
    GET /api/organizations/<id>/
    Full organization detail including all memberships.
    super_admin only — developers cannot inspect other orgs.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if request.user.role != "super_admin":
            return Response(
                {"success": False, "message": "Hanya super admin yang dapat mengakses endpoint ini."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            org = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return Response(
                {"success": False, "message": "Organisasi tidak ditemukan."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OrganizationDetailSerializer(org)
        return Response({"success": True, "organization": serializer.data})
