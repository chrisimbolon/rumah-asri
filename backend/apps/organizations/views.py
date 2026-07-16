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
from apps.core.views import TenantScopedAPIView 
from apps.authentication.models import CustomUser
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

class BuyerListView(TenantScopedAPIView):
    """
    GET /api/organizations/buyers/
    Returns all buyer accounts — used by booking modal
    to populate the buyer dropdown.
    
    Note: TenantScopedAPIView is used for auth,
    but buyers don't have org membership —
    we return all buyers visible to this developer.
    """
    model = None  # override — not a TenantScopedModel query

    def get_queryset(self):
        # Override — buyers don't belong to organizations
        # Return all active buyers
        return CustomUser.objects.filter(
            role="buyer", is_active=True
        ).order_by("full_name")

    def get(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        buyers = self.get_queryset()
        return Response({
            "success": True,
            "count":   buyers.count(),
            "results": [
                {
                    "id":        str(b.id),
                    "full_name": b.full_name,
                    "email":     b.email,
                    "phone":     b.phone,
                }
                for b in buyers
            ],
        })

class AgentListView(TenantScopedAPIView):
    """
    GET /api/organizations/agents/
    Returns developer/agent accounts within the requester's own
    organization(s) — used to populate the Prospect assignment
    dropdown (Prospect.assigned_to only accepts these two roles, see
    ProspectCreateSerializer.validate_assigned_to in apps.crm).

    Unlike BuyerListView above, this IS properly org-scoped — buyers
    genuinely have no org membership concept (that view's own comment
    says so), but agents/developers do (OrganizationMembership), so
    there's no reason to return every agent on the entire platform.
    """
    model = None  # override — not queried via a TenantScopedModel FK

    def get_queryset(self):
        org_ids = self.request.user.memberships.filter(
            is_active=True
        ).values_list("organization_id", flat=True)
        return CustomUser.objects.filter(
            role__in=("developer", "agent"),
            is_active=True,
            memberships__organization_id__in=org_ids,
            memberships__is_active=True,
        ).distinct().order_by("full_name")

    def get(self, request):
        if request.user.role not in ("developer", "agent", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        agents = self.get_queryset()
        return Response({
            "success": True,
            "count":   agents.count(),
            "results": [
                {"id": str(a.id), "full_name": a.full_name, "email": a.email, "role": a.role}
                for a in agents
            ],
        })
