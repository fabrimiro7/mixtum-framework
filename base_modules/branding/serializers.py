from rest_framework import serializers
from .models import BrandingSettings
from .constants import ALLOWED_COLOR_KEYS


class BrandingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandingSettings
        fields = [
            "id",
            "workspace",
            "colors",
            "logo_full",
            "logo_compact",
            "favicon",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "workspace"]

    def validate_colors(self, value):
        if value in (None, ""):
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("colors deve essere un oggetto JSON.")

        invalid_keys = [k for k in value.keys() if k not in ALLOWED_COLOR_KEYS]
        if invalid_keys:
            raise serializers.ValidationError(f"Chiavi non consentite: {', '.join(invalid_keys)}")

        for k, v in value.items():
            if v is not None and not isinstance(v, str):
                raise serializers.ValidationError(f"Valore non valido per {k}.")

        return value

    def _merge_colors(self, current, incoming):
        current = current or {}
        incoming = incoming or {}
        merged = {**current}
        for key, val in incoming.items():
            if val is None:
                merged.pop(key, None)
            else:
                merged[key] = val
        return merged

    def create(self, validated_data):
        if "colors" in validated_data:
            validated_data["colors"] = self._merge_colors({}, validated_data.get("colors"))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "colors" in validated_data:
            instance.colors = self._merge_colors(instance.colors or {}, validated_data.get("colors"))
            validated_data.pop("colors", None)
        return super().update(instance, validated_data)
