# =============================================================================
# === backend/apps/projects/serializers.py ===
# =============================================================================
"""
DevelopIndo — Projects Serializers
"""
from rest_framework import serializers

from .models import Project, ProjectRequirementStatus, StageRequirement


class ProjectSerializer(serializers.ModelSerializer):
    """Full read serializer — includes intelligence fields."""
    units_sold        = serializers.SerializerMethodField()
    overall_progress  = serializers.SerializerMethodField()
    stage_display     = serializers.CharField(read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    # Intelligence fields
    readiness_score   = serializers.IntegerField(read_only=True)
    blocking_count    = serializers.IntegerField(read_only=True)
    next_action       = serializers.CharField(read_only=True, allow_null=True)
    risk_level        = serializers.CharField(read_only=True)
    risk_level_display = serializers.CharField(read_only=True)
    trend             = serializers.CharField(read_only=True)
    can_advance       = serializers.BooleanField(read_only=True)
    next_stage        = serializers.CharField(read_only=True, allow_null=True)
    stage_checklist   = serializers.ListField(read_only=True)

    class Meta:
        model  = Project
        fields = [
            # Identity
            "id", "name", "location", "description",
            # Lifecycle
            "stage", "stage_display", "can_advance", "next_stage",
            "stage_checklist",
            # Intelligence
            "readiness_score", "blocking_count", "next_action",
            "risk_level", "risk_level_display", "trend",
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
    """POST /api/projects/ — creates at DRAFT stage. Only name+location required."""

    class Meta:
        model  = Project
        fields = ["name", "location", "description"]

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Nama proyek minimal 3 karakter.")
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
    """PUT /api/projects/<id>/ — stage not writable here, use advance endpoint."""

    class Meta:
        model  = Project
        fields = [
            "name", "location", "description",
            "total_units", "target_budget",
            "start_date", "end_date",
            "master_plan_url", "site_plan_url",
            "ipr_status", "ipr_date",
            "amdal_status", "amdal_date",
            "pbg_status", "pbg_date",
        ]

    def validate(self, data):
        from datetime import date
        # Auto-set PBG date when approved
        if (data.get("pbg_status") == Project.PermitStatus.APPROVED
                and not data.get("pbg_date")
                and self.instance
                and not self.instance.pbg_date):
            data["pbg_date"] = date.today()
        return data


class ProjectAdvanceSerializer(serializers.Serializer):
    """POST /api/projects/<id>/advance/"""
    confirm = serializers.BooleanField(required=True)

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError(
                "Konfirmasi diperlukan untuk melanjutkan tahap proyek."
            )
        return value
