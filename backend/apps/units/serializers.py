# =============================================================================
# === apps/units/serializers.py ===
# =============================================================================
"""
RumahAsri — Units Serializers
"""
from rest_framework import serializers

from .models import Unit


class UnitSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    project_name    = serializers.CharField(source="project.name",    read_only=True)
    buyer_name      = serializers.CharField(source="buyer.full_name", read_only=True)
    buyer_email     = serializers.CharField(source="buyer.email",     read_only=True)

    class Meta:
        model  = Unit
        fields = [
            "id", "unit_number", "unit_type",
            "land_area", "building_area", "price",
            "status", "status_display",
            "progress", "current_phase", "target_completion",
            "payment_method", "bank",
            "project", "project_name",
            "buyer", "buyer_name", "buyer_email",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UnitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Unit
        fields = [
            "project", "unit_number", "unit_type",
            "land_area", "building_area", "price",
            "status", "progress", "current_phase",
            "target_completion", "payment_method", "bank",
            "buyer",
        ]

    def validate_project(self, project):
        """
        THE FIX: previously a developer could POST any project UUID,
        including one belonging to a different organization, and the
        unit would be silently created inside it. Now it's rejected
        here, before save() ever runs.
        """
        user = self.context["request"].user
        if user.role == "super_admin":
            return project
        org_ids = user.memberships.filter(is_active=True).values_list(
            "organization_id", flat=True
        )
        if project.organization_id not in org_ids:
            raise serializers.ValidationError("Anda tidak memiliki akses ke proyek ini.")
        return project