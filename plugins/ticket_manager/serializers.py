from rest_framework import serializers
from base_modules.user_manager.serializers import UserDetailSerializer, UserDetailSerializer
from base_modules.attachment.serializers import AttachmentSerializer
from .models import Ticket, Message, Attachment

class LinkedTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'title', 'status',]


class TicketSerializer(serializers.ModelSerializer):
    client = UserDetailSerializer()
    assignees = UserDetailSerializer(many=True)
    attachments = AttachmentSerializer(many=True)
    ticket_linked = LinkedTicketSerializer()

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


