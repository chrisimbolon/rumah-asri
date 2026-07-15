# =============================================================================
# === backend/apps/crm/serializers.py ===
# CRM Foundation Sprint 2.5: Prospect CRUD serializers.
# =============================================================================
from rest_framework import serializers

from apps.units.models import Unit

from .models import Activity, CustomerProfile, Prospect, SiteVisit


class ProspectSerializer(serializers.ModelSerializer):
    """Read serializer — same shape convention as UnitSerializer:
    denormalized display fields alongside raw FK ids, nothing the
    frontend has to join client-side."""
    status_display       = serializers.CharField(source="get_status_display", read_only=True)
    project_name          = serializers.CharField(source="interested_project.name", read_only=True, default=None)
    assigned_to_name       = serializers.CharField(source="assigned_to.full_name", read_only=True, default=None)
    converted_booking_id  = serializers.UUIDField(source="converted_booking.id", read_only=True, default=None)

    class Meta:
        model  = Prospect
        fields = [
            "id", "name", "phone", "source",
            "interested_project", "project_name",
            "assigned_to", "assigned_to_name",
            "status", "status_display",
            "next_followup_date", "notes",
            "converted_booking_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "converted_booking_id", "created_at", "updated_at"]


class ProspectCreateSerializer(serializers.ModelSerializer):
    """
    Used for both POST (create) and PUT (partial update) — same
    pattern UnitCreateSerializer already establishes for Unit.

    Deliberately excludes `converted_booking`: that field is only ever
    set by UnitBookingView.post()'s Sprint 2 conversion wiring, never
    directly through this API. Writing it here would let a client
    fake a conversion without a real Booking behind it.
    """

    class Meta:
        model  = Prospect
        fields = [
            "name", "phone", "source",
            "interested_project", "assigned_to",
            "status", "next_followup_date", "notes",
        ]

    def validate_interested_project(self, project):
        """Same tenant-membership check as UnitCreateSerializer.validate_project —
        a user can't attach a prospect to a project outside their org."""
        if project is None:
            return project
        user = self.context["request"].user
        if user.role == "super_admin":
            return project
        org_ids = user.memberships.filter(is_active=True).values_list(
            "organization_id", flat=True
        )
        if project.organization_id not in org_ids:
            raise serializers.ValidationError(
                "Anda tidak memiliki akses ke proyek ini."
            )
        return project

    def validate_assigned_to(self, user):
        """
        API-level enforcement of the same rule the model's
        limit_choices_to only hints at for admin/forms — see the
        comment on Prospect.assigned_to in models.py. Org-membership
        of the assignee isn't checked here (would require knowing the
        prospect's resolved organization, which isn't settled until
        create()/save() below) — a known, narrow gap, not a silent one.
        """
        if user is None:
            return user
        if user.role not in ("developer", "agent"):
            raise serializers.ValidationError(
                "Hanya developer atau agent yang dapat ditugaskan sebagai penanggung jawab."
            )
        return user

    def create(self, validated_data):
        """
        Sprint 1's _resolve_organization() only fires when
        interested_project is set. Since it's optional here (unlike
        Unit's required project), organization is resolved explicitly
        in the serializer instead of relying on model-level magic —
        same reasoning ProjectCreateSerializer.create() already
        applies to Project, which has no parent relation to derive
        from at all.
        """
        request = self.context["request"]
        project = validated_data.get("interested_project")

        if project is not None:
            organization = project.organization
        else:
            membership = request.user.memberships.filter(is_active=True).first()
            if membership is None:
                raise serializers.ValidationError({
                    "organization": "Anda tidak tergabung dalam organisasi manapun."
                })
            organization = membership.organization

        return Prospect.objects.create(organization=organization, **validated_data)


class ActivitySerializer(serializers.ModelSerializer):
    """
    Sprint 4 (CRM Foundation Phase B). `prospect`, `organization`, and
    `created_by` are all set server-side in ActivityListView.post() —
    never client-writable — same discipline ProspectCreateSerializer
    already applies to `converted_booking`.
    """
    activity_type_display = serializers.CharField(source="get_activity_type_display", read_only=True)
    created_by_name        = serializers.CharField(source="created_by.full_name", read_only=True, default=None)

    class Meta:
        model  = Activity
        fields = [
            "id", "activity_type", "activity_type_display",
            "notes", "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_by_name", "created_at"]


class SiteVisitSerializer(serializers.ModelSerializer):
    """
    Sprint 6 (CRM Foundation Phase B). Single serializer for both
    scheduling (POST) and status/reschedule updates (PUT) — same
    pattern ProspectCreateSerializer already establishes. `prospect`,
    `organization`, and `created_by` are all set server-side in the
    view, never client-writable.
    """
    status_display  = serializers.CharField(source="get_status_display", read_only=True)
    unit_number     = serializers.CharField(source="unit.unit_number", read_only=True, default=None)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True, default=None)

    class Meta:
        model  = SiteVisit
        fields = [
            "id", "unit", "unit_number", "scheduled_at",
            "status", "status_display", "notes",
            "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_by_name", "created_at"]

    def validate_unit(self, unit):
        """Same tenant-membership check as ProspectCreateSerializer's
        validate_interested_project — a visit can't be scheduled
        against a unit outside the requester's org."""
        if unit is None:
            return unit
        user = self.context["request"].user
        if user.role == "super_admin":
            return unit
        org_ids = user.memberships.filter(is_active=True).values_list(
            "organization_id", flat=True
        )
        if unit.organization_id not in org_ids:
            raise serializers.ValidationError(
                "Anda tidak memiliki akses ke unit ini."
            )
        return unit


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Sprint 8 (CRM Foundation Phase B). unit_number/project_name are
    read-only, computed at request time — the join for display the
    model's own docstring explicitly says it should never own. If the
    same buyer somehow has multiple units in this org, this shows the
    first one found; genuinely rare in practice (one buyer usually
    buys once), and not worth a real multi-unit list UI this sprint.
    """
    user_name    = serializers.CharField(source="user.full_name", read_only=True)
    user_email   = serializers.CharField(source="user.email", read_only=True)
    unit_number  = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()

    class Meta:
        model  = CustomerProfile
        fields = [
            "id", "user", "user_name", "user_email",
            "budget", "family_notes", "timeline_notes",
            "unit_number", "project_name",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "user", "user_name", "user_email",
            "unit_number", "project_name", "created_at", "updated_at",
        ]

    def _buyer_unit(self, obj):
        return Unit.objects.filter(
            buyer=obj.user, organization=obj.organization
        ).select_related("project").first()

    def get_unit_number(self, obj):
        unit = self._buyer_unit(obj)
        return unit.unit_number if unit else None

    def get_project_name(self, obj):
        unit = self._buyer_unit(obj)
        return unit.project.name if unit else None
