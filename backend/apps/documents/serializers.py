"""
DevelopIndo — Documents Serializers
"""

from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    status_display   = serializers.CharField(source="get_status_display",   read_only=True)
    doc_type_display = serializers.CharField(source="get_doc_type_display", read_only=True)
    unit_number      = serializers.CharField(source="unit.unit_number",     read_only=True)
    file_url         = serializers.SerializerMethodField()

    class Meta:
        model  = Document
        fields = [
            "id", "name", "doc_type", "doc_type_display",
            "status", "status_display",
            "file", "file_url", "issued_date",
            "unit_number", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class DocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Document
        fields = ["unit", "doc_type", "name", "file", "status", "issued_date"]

    def validate_unit(self, unit):
        user = self.context["request"].user
        if user.role == "super_admin":
            return unit
        org_ids = user.memberships.filter(is_active=True).values_list(
            "organization_id", flat=True
        )
        if unit.organization_id not in org_ids:
            raise serializers.ValidationError("Anda tidak memiliki akses ke unit ini.")
        return unit