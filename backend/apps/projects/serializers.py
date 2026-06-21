from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_name(self, value: str) -> str:
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("Project name cannot be empty.")
        if len(name) > 255:
            raise serializers.ValidationError("Project name must be at most 255 characters.")
        return name
