from base_modules.user_manager.serializers import UserDetailSerializer
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class AttachmentCreateSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Attachment
        fields = ['id', 'title', 'file', 'description']
        read_only_fields = ['author', 'creation_date']


class AttachmentSerializer(serializers.ModelSerializer):
   
    author = UserDetailSerializer()
    
    class Meta:
        model = Attachment
        fields = ['id', 'title', 'author', 'creation_date', 'file', 'description']
        read_only_fields = ['author', 'creation_date']

class AttachmentEditSerializer(serializers.ModelSerializer):
       
    class Meta:
        model = Attachment
        fields = ['id', 'title', 'author', 'creation_date', 'file', 'description']
        read_only_fields = ['author', 'creation_date']