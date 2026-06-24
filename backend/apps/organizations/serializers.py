# =============================================================================
# === backend/apps/organizations/serializers.py ===
# =============================================================================
"""
DevelopIndo — Organizations Serializers

Three levels of detail:
  OrganizationSerializer       — list view (counts only, no nested data)
  OrganizationMemberSerializer — membership rows
  OrganizationDetailSerializer — full detail with memberships
"""
from rest_framework import serializers
from .models import Organization, OrganizationMembership
from apps.authentication.models import CustomUser


class MemberUserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomUser
        fields = ["id", "email", "full_name", "role", "is_active"]


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user = MemberUserSerializer(read_only=True)

    class Meta:
        model  = OrganizationMembership
        fields = ["id", "user", "role", "is_active", "created_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    member_count  = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()

    class Meta:
        model  = Organization
        fields = [
            "id", "name", "plan", "is_active",
            "member_count", "project_count", "created_at",
        ]

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()

    def get_project_count(self, obj):
        # Avoids importing Project at module level — keeps circular imports clean
        from apps.projects.models import Project
        return Project.objects.filter(organization=obj).count()


class OrganizationDetailSerializer(OrganizationSerializer):
    memberships = OrganizationMemberSerializer(many=True, read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ["memberships"]
