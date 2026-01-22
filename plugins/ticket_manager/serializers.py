from plugins.project_manager.models import Project
from rest_framework import serializers
from base_modules.user_manager.models import User
from base_modules.user_manager.serializers import UserDetailSerializer
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
    last_message = serializers.SerializerMethodField(read_only=True)
    last_read_at = serializers.SerializerMethodField(read_only=True)
    has_unread = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'client', 'project', 'assignees', 'priority',
            'hours_estimation', 'opening_date', 'closing_date', 'cost_estimation', 'status',
            'expected_resolution_date', 'expected_action', 'real_action', 'attachments',
            'ticket_workspace', 'ticket_linked', 'ticket_type', 'payments_status', 'sla_due_at',
            'last_message', 'last_read_at', 'has_unread',
        ]

    def get_last_message(self, obj):
        # related_name 'ticket' on Message -> Ticket: obj.ticket = RelatedManager of Message
        lm = obj.ticket.order_by('-insert_date').select_related('author').first()
        if not lm:
            return None
        return {
            'id': lm.id,
            'insert_date': lm.insert_date.isoformat() if lm.insert_date else None,
            'author': {'id': lm.author.id, 'permission': lm.author.permission},
        }

    def get_last_read_at(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return None
        tr = obj.read_by_users.filter(user=request.user).first()
        return tr.last_read_at.isoformat() if tr else None

    def get_has_unread(self, obj):
        lm = obj.ticket.order_by('-insert_date').first()
        if not lm:
            return False
        request = self.context.get('request')
        if not request or not request.user:
            return False
        tr = obj.read_by_users.filter(user=request.user).first()
        last_read = tr.last_read_at if tr else None
        if last_read is None:
            return True
        return lm.insert_date > last_read


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

class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer per la creazione di task (campi scrivibili, assignee come ID)."""
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            'project',
            'ticket',
            'title',
            'description',
            'assignee',
            'status',
            'priority',
            'estimate_hours',
            'start_date',
            'due_date',
        ]
        extra_kwargs = {
            'title': {'required': True},
            'ticket': {'required': False, 'allow_null': True},
            'status': {'default': 'todo'},
            'priority': {'default': 'medium'},
        }


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
