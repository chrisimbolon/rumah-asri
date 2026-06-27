# =============================================================================
# === backend/apps/projects/serializers.py ===
# Sprint 2: adds RequirementEvidenceSerializer
# All Sprint 1 serializers preserved — additive only.
# =============================================================================
from datetime import date

from rest_framework import serializers

from .models import Project, ProjectRequirementStatus, RequirementEvidence, StageRequirement


# =============================================================================
# Sprint 2: NEW serializer
# =============================================================================

class RequirementEvidenceSerializer(serializers.ModelSerializer):
    """Read serializer for RequirementEvidence."""
    uploaded_by_name  = serializers.CharField(
        source="uploaded_by.full_name", read_only=True, default=""
    )
    verifier_name     = serializers.CharField(
        source="verifier.full_name", read_only=True, default=""
    )
    verification_display = serializers.CharField(
        source="get_verification_status_display", read_only=True
    )
    file_url_display  = serializers.SerializerMethodField()

    class Meta:
        model  = RequirementEvidence
        fields = [
            "id",
            "file_name", "file_url", "file_url_display",
            "notes",
            "uploaded_by", "uploaded_by_name", "uploaded_at",
            "verification_status", "verification_display",
            "verifier", "verifier_name", "verified_at",
            "verifier_notes",
        ]
        read_only_fields = ["id", "uploaded_at", "verified_at"]

    def get_file_url_display(self, obj):
        """Returns the file download URL or external URL."""
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return obj.file_url or ""


# =============================================================================
# Original serializers — UNCHANGED from Sprint 1
# =============================================================================

class ProjectSerializer(serializers.ModelSerializer):
    """Full read serializer — includes all intelligence fields."""

    units_sold         = serializers.SerializerMethodField()
    overall_progress   = serializers.SerializerMethodField()
    stage_display      = serializers.CharField(read_only=True)
    organization_name  = serializers.CharField(source="organization.name", read_only=True)

    # Original intelligence fields
    readiness_score    = serializers.IntegerField(read_only=True)
    blocking_count     = serializers.IntegerField(read_only=True)
    next_action        = serializers.CharField(read_only=True, allow_null=True)
    risk_level         = serializers.CharField(read_only=True)
    risk_level_display = serializers.CharField(read_only=True)
    trend              = serializers.CharField(read_only=True)
    can_advance        = serializers.BooleanField(read_only=True)
    next_stage         = serializers.CharField(read_only=True, allow_null=True)
    stage_checklist    = serializers.ListField(read_only=True)

    # Sprint 1 intelligence fields
    readiness_dimensions  = serializers.DictField(read_only=True)
    risk_reasons          = serializers.ListField(read_only=True)
    alerts                = serializers.ListField(read_only=True)
    parallel_stages       = serializers.DictField(
        source="parallel_stage_status", read_only=True
    )
    collection_efficiency = serializers.DictField(read_only=True)

    class Meta:
        model  = Project
        fields = [
            "id", "name", "location", "description",
            "stage", "stage_display", "can_advance", "next_stage",
            "stage_checklist",
            "readiness_score", "blocking_count", "next_action",
            "risk_level", "risk_level_display", "trend",
            "readiness_dimensions", "risk_reasons",
            "alerts", "parallel_stages", "collection_efficiency",
            "is_selling", "is_constructing",
            "total_units", "units_sold", "overall_progress",
            "target_budget", "start_date", "end_date",
            "master_plan_url", "site_plan_url",
            "ipr_status", "ipr_date",
            "amdal_status", "amdal_date",
            "pbg_status", "pbg_date",
            "organization_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_units_sold(self, obj):
        return obj.units_sold

    def get_overall_progress(self, obj):
        return obj.overall_progress


class ProjectCreateSerializer(serializers.ModelSerializer):
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
            "is_selling", "is_constructing",
        ]

    def validate(self, data):
        if (data.get("pbg_status") == Project.PermitStatus.APPROVED
                and not data.get("pbg_date")
                and self.instance
                and not self.instance.pbg_date):
            data["pbg_date"] = date.today()
        return data


class ProjectAdvanceSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(required=True)

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError(
                "Konfirmasi diperlukan untuk melanjutkan tahap proyek."
            )
        return value
