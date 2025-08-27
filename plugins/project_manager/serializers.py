from rest_framework import serializers
from base_modules.user_manager.serializers import UserDetailSerializer
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = '__all__'

class ProjectSerializerGet(serializers.ModelSerializer):

    client = UserDetailSerializer()
    contributors = UserDetailSerializer(many=True)
    class Meta:
        model = Project
        fields = '__all__'



