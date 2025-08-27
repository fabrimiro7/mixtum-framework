from rest_framework import serializers
from base_modules.user_manager.serializers import UserDetailSerializer
from plugins.project_manager.serializers import ProjectSerializer
from .models import Tutorial, Note, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'description', 'parent', 'subcategories']
        depth = 1
    
class TutorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutorial
        fields = '__all__'


class TutorialFullSerializer(serializers.ModelSerializer):

    author = UserDetailSerializer()
    category = CategorySerializer(many=True)

    class Meta:
        model = Tutorial
        fields = '__all__'

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'text', 'last_modified', 'user', 'tutorial']

