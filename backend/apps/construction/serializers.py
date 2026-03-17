"""
RumahAsri — Construction Serializers
"""

from rest_framework import serializers

from .models import ConstructionPhase, ConstructionPhoto


class ConstructionPhotoSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)

    class Meta:
        model  = ConstructionPhoto
        fields = ["id", "image", "caption", "uploaded_by_name", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class ConstructionPhaseSerializer(serializers.ModelSerializer):
    status_display   = serializers.CharField(source="get_status_display", read_only=True)
    updated_by_name  = serializers.CharField(source="updated_by.full_name", read_only=True)
    photos           = ConstructionPhotoSerializer(many=True, read_only=True)

    class Meta:
        model  = ConstructionPhase
        fields = [
            "id", "phase_order", "phase_name", "phase_date",
            "status", "status_display", "notes",
            "updated_by_name", "photos",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ConstructionPhaseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ConstructionPhase
        fields = ["phase_date", "status", "notes"]