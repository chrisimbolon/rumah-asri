# =============================================================================
# === backend/apps/commissions/views.py ===
# Commission Foundation Sprint 1.
# =============================================================================
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import Commission, CommissionPolicy, CommissionTier
from .serializers import CommissionPolicySerializer, CommissionSerializer, CommissionTierSerializer


class CommissionPolicyView(TenantScopedAPIView):
    """
    GET/PUT /api/commissions/policy/
    Single object per org, not a list — get_or_create ensures every
    org has a policy the moment they first touch this endpoint,
    defaulting to a 0-value rate (no real commission gets computed
    until an admin actually sets a real rate_value).
    """
    model = CommissionPolicy

    def _get_or_create_policy(self, request):
        if request.user.role == "super_admin":
            # super_admin has no single "their" org — this endpoint
            # doesn't make sense without one.
            return None
        membership = request.user.memberships.filter(is_active=True).first()
        if membership is None:
            return None
        policy, _ = CommissionPolicy.objects.get_or_create(organization=membership.organization)
        return policy

    def get(self, request):
        policy = self._get_or_create_policy(request)
        if policy is None:
            return Response(
                {"success": False, "message": "Tidak ada organisasi aktif."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"success": True, "policy": CommissionPolicySerializer(policy).data})

    def put(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        policy = self._get_or_create_policy(request)
        if policy is None:
            return Response(
                {"success": False, "message": "Tidak ada organisasi aktif."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CommissionPolicySerializer(policy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Kebijakan komisi berhasil diperbarui",
                "policy":  CommissionPolicySerializer(policy).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CommissionListView(TenantScopedAPIView):
    """
    GET /api/commissions/
    Agents see only their own commissions — mirrors the buyer
    portal's own-identity scoping. Developer/super_admin see every
    commission in the org.
    """
    model = Commission

    def get(self, request):
        commissions = self.get_queryset().select_related("agent", "booking", "booking__unit")
        if request.user.role == "agent":
            commissions = commissions.filter(agent=request.user)
        status_filter = request.query_params.get("status")
        if status_filter:
            commissions = commissions.filter(status=status_filter)
        serializer = CommissionSerializer(commissions, many=True)
        return Response({
            "success": True,
            "count":   commissions.count(),
            "results": serializer.data,
        })


class CommissionDetailView(TenantScopedAPIView):
    """
    GET/PUT /api/commissions/<id>/
    PUT is deliberately staff-only (developer/super_admin) — an agent
    marking their OWN commission "paid" would be self-certified
    bookkeeping, not a real control. Agents can still GET their own
    row for visibility, same scoping as the list view.
    """
    model = Commission

    def get(self, request, pk):
        commission = self.get_object(pk)
        if request.user.role == "agent" and commission.agent_id != request.user.id:
            return Response(
                {"success": False, "message": "Tidak ditemukan, atau Anda tidak memiliki akses."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"success": True, "commission": CommissionSerializer(commission).data})

    def put(self, request, pk):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        commission = self.get_object(pk)
        serializer = CommissionSerializer(commission, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success":    True,
                "message":    "Status komisi berhasil diperbarui",
                "commission": CommissionSerializer(commission).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CommissionTierListView(TenantScopedAPIView):
    """
    GET  /api/commissions/policy/tiers/
    POST /api/commissions/policy/tiers/
    Sprint 2 (Commission Foundation). Tiers always belong to the
    requester's own org policy — resolved the same way
    CommissionPolicyView does, never accepted as client input.
    """
    model = CommissionTier

    def _get_or_create_policy(self, request):
        if request.user.role == "super_admin":
            return None
        membership = request.user.memberships.filter(is_active=True).first()
        if membership is None:
            return None
        policy, _ = CommissionPolicy.objects.get_or_create(organization=membership.organization)
        return policy

    def get(self, request):
        policy = self._get_or_create_policy(request)
        if policy is None:
            return Response(
                {"success": False, "message": "Tidak ada organisasi aktif."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tiers = policy.tiers.all()
        serializer = CommissionTierSerializer(tiers, many=True)
        return Response({"success": True, "count": tiers.count(), "results": serializer.data})

    def post(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        policy = self._get_or_create_policy(request)
        if policy is None:
            return Response(
                {"success": False, "message": "Tidak ada organisasi aktif."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CommissionTierSerializer(data=request.data, context={"policy": policy})
        if serializer.is_valid():
            tier = serializer.save(policy=policy, organization=policy.organization)
            return Response({
                "success": True,
                "message": "Tingkat komisi berhasil ditambahkan",
                "tier":    CommissionTierSerializer(tier).data,
            }, status=status.HTTP_201_CREATED)
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CommissionTierDetailView(TenantScopedAPIView):
    """PUT/DELETE /api/commissions/policy/tiers/<id>/"""
    model = CommissionTier

    def put(self, request, pk):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        tier = self.get_object(pk)
        serializer = CommissionTierSerializer(tier, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Tingkat komisi berhasil diperbarui",
                "tier":    CommissionTierSerializer(tier).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        tier = self.get_object(pk)
        tier.delete()
        return Response({"success": True, "message": "Tingkat komisi berhasil dihapus"})
