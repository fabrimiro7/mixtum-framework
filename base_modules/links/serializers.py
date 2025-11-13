from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Link, LINK_LABEL_CHOICES


class LinkSerializer(serializers.ModelSerializer):
    # Expose target info in a friendly way; allow posting content_type by id or natural key.
    content_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all(),
        source="content_type",
        write_only=True,
        required=True,
    )
    content_type = serializers.SlugRelatedField(
        read_only=True, slug_field="model"
    )
    app_label = serializers.SerializerMethodField(read_only=True)
    label_display = serializers.CharField(source="get_label_display", read_only=True)

    class Meta:
        model = Link
        fields = (
            "id",
            "label",
            "label_display",
            "title",
            "description",
            "url",
            "content_type_id",
            "content_type",
            "app_label",
            "object_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_app_label(self, obj):
        return obj.content_type.app_label

    def validate_label(self, value):
        valid = {c[0] for c in LINK_LABEL_CHOICES}
        if value not in valid:
            raise serializers.ValidationError("Invalid label.")
        return value
