from rest_framework import serializers
from base_modules.user_manager.models import User
from base_modules.user_manager.serializers import UserDetailSerializer
from plugins.project_manager.models import Project
from .models import Phase


class PhaseCreateSerializer(serializers.ModelSerializer):
    """Serializer per la creazione di fasi (campi scrivibili, owner come ID)."""
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Phase
        fields = [
            'project',
            'title',
            'description',
            'owner',
            'status',
            'priority',
            'start_date',
            'due_date',
        ]
        extra_kwargs = {
            'title': {'required': True},
            'status': {'default': 'todo'},
            'priority': {'default': 'medium'},
        }


class PhaseSerializer(serializers.ModelSerializer):
    owner = UserDetailSerializer()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    project = serializers.SerializerMethodField()

    def get_project(self, obj):
        return {
            'id': obj.project.id if obj.project else None,
            'title': obj.project.title if obj.project else None,
        }

    class Meta:
        model = Phase
        fields = [
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'owner',
            'project',
            'start_date',
            'due_date',
            'project_id',
            'created_at',
            'updated_at',
        ]
