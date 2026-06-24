# =============================================================================
# === backend/apps/projects/serializers.py ===
# =============================================================================
"""
DevelopIndo — Projects Serializers
"""
from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """Full read serializer — used for list and detail responses."""
    units_sold       = serializers.SerializerMethodField()
    overall_progress = serializers.SerializerMethodField()
    stage_display    = serializers.CharField(read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    can_advance      = serializers.BooleanField(read_only=True)
    next_stage       = serializers.CharField(read_only=True)
    stage_checklist  = serializers.ListField(read_only=True)

    class Meta:
        model  = Project
        fields = [
            # Identity
            "id", "name", "location", "description",
            # Lifecycle
            "stage", "stage_display", "can_advance", "next_stage",
            "stage_checklist",
            # Planning
            "total_units", "units_sold", "overall_progress",
            "target_budget", "start_date", "end_date",
            "master_plan_url", "site_plan_url",
            # Permits
            "ipr_status", "ipr_date",
            "amdal_status", "amdal_date",
            "pbg_status", "pbg_date",
            # Meta
            "organization_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_units_sold(self, obj):
        return obj.units_sold

    def get_overall_progress(self, obj):
        return obj.overall_progress


class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Used for POST /api/projects/ — creates a project at DRAFT stage.
    Only name and location are required. Everything else is optional
    so a developer can get started immediately with minimal friction.
    """
    class Meta:
        model  = Project
        fields = [
            "name", "location", "description",
        ]

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Nama proyek minimal 3 karakter."
            )
        return value.strip()

    def create(self, validated_data):
        user = self.context["request"].user
        membership = user.memberships.filter(is_active=True).first()
        if not membership:
            raise serializers.ValidationError(
                "Anda belum tergabung dalam organisasi developer manapun."
            )
        validated_data["organization"] = membership.organization
        validated_data["stage"]        = Project.Stage.DRAFT
        return super().create(validated_data)


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """
    Used for PUT /api/projects/<id>/ — updates project data.
    Stage is NOT writable here — use the advance endpoint instead.
    """
    class Meta:
        model  = Project
        fields = [
            "name", "location", "description",
            "total_units", "target_budget",
            "start_date", "end_date",
            "master_plan_url", "site_plan_url",
            # Permit fields
            "ipr_status", "ipr_date",
            "amdal_status", "amdal_date",
            "pbg_status", "pbg_date",
        ]

    def validate(self, data):
        """
        If PBG is being set to approved, record the date automatically
        if not provided.
        """
        from datetime import date
        if (data.get("pbg_status") == Project.PermitStatus.APPROVED
                and not data.get("pbg_date")
                and not self.instance.pbg_date):
            data["pbg_date"] = date.today()
        return data


class ProjectAdvanceSerializer(serializers.Serializer):
    """
    Used for POST /api/projects/<id>/advance/
    Confirms the developer wants to move to the next stage.
    """
    confirm = serializers.BooleanField(required=True)

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError(
                "Konfirmasi diperlukan untuk melanjutkan tahap proyek."
            )
        return value
