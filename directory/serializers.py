from django.utils.html import strip_tags
from rest_framework import serializers

from directory.models import WasteBank


class WasteBankSerializer(serializers.ModelSerializer):

    class Meta:
        model = WasteBank
        fields = [
            "id",
            "name",
            "address",
            "contact_number",
            "email",
            "is_osm",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = strip_tags(value).strip()

        if not value:
            raise serializers.ValidationError(
                "Waste bank name cannot be empty."
            )
        return value

    def validate_address(self, value):
        value = strip_tags(value).strip()

        if not value:
            raise serializers.ValidationError(
                "Waste bank address cannot be empty."
            )
        return value