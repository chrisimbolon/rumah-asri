# =============================================================================
# === backend/apps/projects/serializers.py ===
# Sprint 2: adds RequirementEvidenceSerializer
# All Sprint 1 serializers preserved — additive only.
# =============================================================================
from datetime import date

from rest_framework import serializers

from .models import Project, ProjectRequirementStatus, RequirementComment, RequirementEvidence, StageRequirement

class RequirementCommentSerializer(serializers.ModelSerializer):
    author_name  = serializers.SerializerMethodField()
    author_email = serializers.SerializerMethodField()

    class Meta:
        model  = RequirementComment
        fields = [
            "id", "body",
            "author", "author_name", "author_email",
            "created_at",
        ]
        read_only_fields = ["id", "author", "author_name", "author_email", "created_at"]

    def get_author_name(self, obj):
        return obj.author.full_name if obj.author else "?"

    def get_author_email(self, obj):
        return obj.author.email if obj.author else ""
# =============================================================================
# Sprint 8: NEW serializer
# =============================================================================

class RequirementEvidenceSerializer(serializers.ModelSerializer):
    """
    Sprint 8: Extended read serializer for RequirementEvidence.

    New fields:
      version_number    — int (1, 2, 3...)
      version_label     — str ("v1", "v2")
      is_latest         — bool
      superseded_by_id  — UUID or null
      version_chain     — [{id, version_number, status, is_latest, ...}]
      can_verify        — bool (based on request.user)
      cannot_verify_reason — str (why current user can't verify)
      eligible_verifiers   — [{id, full_name}] (who CAN verify)
      uploaded_by_name  — str (unchanged from Sprint 2)
      verifier_name     — str (unchanged from Sprint 2)
      verification_display — str (unchanged from Sprint 2)
      file_url_display  — str (unchanged from Sprint 2)
    """
    # ── Sprint 2 fields — UNCHANGED ──────────────────────────
    uploaded_by_name  = serializers.CharField(
        source="uploaded_by.full_name", read_only=True, default="",
    )
    verifier_name     = serializers.CharField(
        source="verifier.full_name", read_only=True, default="",
    )
    verification_display = serializers.CharField(
        source="get_verification_status_display", read_only=True,
    )
    file_url_display  = serializers.SerializerMethodField()

    # ── Sprint 8: version fields ──────────────────────────────
    version_label         = serializers.SerializerMethodField()
    superseded_by_id      = serializers.SerializerMethodField()
    version_chain         = serializers.SerializerMethodField()
    can_verify            = serializers.SerializerMethodField()
    cannot_verify_reason  = serializers.SerializerMethodField()
    eligible_verifiers    = serializers.SerializerMethodField()

    class Meta:
        model  = RequirementEvidence
        fields = [
            # Sprint 2 original fields
            "id",
            "file_name", "file_url", "file_url_display",
            "notes",
            "uploaded_by", "uploaded_by_name", "uploaded_at",
            "verification_status", "verification_display",
            "verifier", "verifier_name", "verified_at",
            "verifier_notes",
            # Sprint 8: version fields
            "version_number",
            "version_label",
            "is_latest",
            "superseded_by_id",
            "version_chain",
            "can_verify",
            "cannot_verify_reason",
            "eligible_verifiers",
        ]
        read_only_fields = ["id", "uploaded_at", "verified_at"]

    def get_file_url_display(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return obj.file_url or ""

    def get_version_label(self, obj):
        return f"v{obj.version_number}"

    def get_superseded_by_id(self, obj):
        return str(obj.superseded_by.id) if obj.superseded_by else None

    def get_version_chain(self, obj):
        """Full version history for this requirement — oldest → newest."""
        return obj.get_version_chain()

    def get_can_verify(self, obj):
        """
        Sprint 8: Can the current request user verify this evidence?
        Returns True/False based on:
          - status is pending
          - is_latest = True
          - user is org member
          - user != uploader
        """
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return False
        can, _ = obj.can_verify(request.user)
        return can

    def get_cannot_verify_reason(self, obj):
        """Sprint 8: Human-readable reason why current user cannot verify."""
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return "Tidak terautentikasi"
        _, reason = obj.can_verify(request.user)
        return reason

    def get_eligible_verifiers(self, obj):
        """
        Sprint 8: List of org members who CAN verify this evidence.
        Only populated for pending + is_latest evidence to avoid N+1.
        Returns empty list for approved/rejected evidence.
        """
        if obj.verification_status != RequirementEvidence.VerificationStatus.PENDING:
            return []
        if not obj.is_latest:
            return []
        eligible = obj.get_eligible_verifiers()
        return [
            {"id": str(m.id), "full_name": m.full_name}
            for m in eligible[:5]  # cap at 5 for display
        ]


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
