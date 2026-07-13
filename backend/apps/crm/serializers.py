# =============================================================================
# === backend/apps/crm/serializers.py ===
# CRM Foundation Sprint 2.5: Prospect CRUD serializers.
# =============================================================================
from rest_framework import serializers

from .models import Prospect


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
