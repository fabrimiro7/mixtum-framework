# workspace/serializers.py
from base_modules.user_manager.models import User
from rest_framework import serializers
from .models import Workspace, WorkspaceUser

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer di base per il modello User (per riferimento).
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email'] 

class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Serializer per il modello Workspace.
    """
    users_count = serializers.SerializerMethodField()
    
    def get_users_count(self, obj):
        return obj.workspaceuser_set.count()

    class Meta:
        model = Workspace
        fields = [
            'id',
            'workspace_name',
            'workspace_description',
            'workspace_logo',
            'created_at',
            'updated_at',
            'users_count' 
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class WorkspaceUserSerializer(serializers.ModelSerializer):
    """
    Serializer per il modello WorkspaceUser.
    """
    user = UserSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    workspace_id = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(), source='workspace', write_only=True
    )

    class Meta:
        model = WorkspaceUser
        fields = [
            'id',
            'user',
            'workspace',
            'user_id',      
            'workspace_id', 
            'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']

    def create(self, validated_data):
        return super().create(validated_data)

