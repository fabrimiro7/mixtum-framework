from rest_framework import serializers

from base_modules.user_manager.serializers import UserDetailSerializer
from plugins.project_manager.serializers import ProjectSerializer
from .models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):

    customer = UserDetailSerializer()
    project = ProjectSerializer(many=True)
        
    class Meta:
        model = Subscription
        fields = '__all__'

class SubscriptionSerializerAdd(serializers.ModelSerializer):
       
    class Meta:
        model = Subscription
        fields = '__all__'

