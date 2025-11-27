from plugins.project_manager.models import Project
from rest_framework import serializers
from base_modules.user_manager.serializers import UserDetailSerializer, UserDetailSerializer
from base_modules.attachment.serializers import AttachmentSerializer
from .models import Ticket, Message, Attachment, Task

class LinkedTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'title', 'status',]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title']


class TicketSerializer(serializers.ModelSerializer):
    client = UserDetailSerializer()
    assignees = UserDetailSerializer(many=True)
    attachments = AttachmentSerializer(many=True)
    ticket_linked = LinkedTicketSerializer()
    project = ProjectSerializer()

    class Meta:
        model = Ticket
        fields = '__all__'


class TicketPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = '__all__'

class MessageFullSerializer(serializers.ModelSerializer):

    author = UserDetailSerializer()
    attachments = AttachmentSerializer(many=True)

    class Meta:
        model = Message
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    assignee = UserDetailSerializer()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'assignee',
            'estimate_hours',
            'start_date',
            'due_date',
            'ticket_id',
            'project_id',
            'created_at',
            'updated_at',
        ]
