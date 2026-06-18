# =============================================================================
# === apps/projects/serializers.py ===
# =============================================================================
"""
RumahAsri — Projects Serializers
"""
from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    units_sold        = serializers.SerializerMethodField()
    overall_progress   = serializers.SerializerMethodField()
    status_display      = serializers.CharField(source="get_status_display", read_only=True)
    organization_name  = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model  = Project
        fields = [
            "id", "name", "location", "description",
            "status", "status_display",
            "total_units", "units_sold", "overall_progress",
            "start_date", "end_date",
            "organization_name", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_units_sold(self, obj):
        return obj.units_sold

    def get_overall_progress(self, obj):
        return obj.overall_progress


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Project
        fields = [
            "name", "location", "description",
            "status", "total_units",
            "start_date", "end_date",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        membership = user.memberships.filter(is_active=True).first()
        if not membership:
            raise serializers.ValidationError(
                "Anda belum tergabung dalam organisasi developer manapun."
            )
        validated_data["organization"] = membership.organization
        return super().create(validated_data)