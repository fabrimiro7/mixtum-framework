from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # adatta come preferisci
from django.db import transaction

from .models import Email, EmailTemplate, EmailStatus
from .serializers import (
    EmailSerializer, EmailTemplateSerializer, EmailSendSerializer
)
from .services import send_email

class EmailTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD sui template email.
    """
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated]

class EmailViewSet(viewsets.ModelViewSet):
    """
    CRUD sulle email. Include azione 'send' per inviare una email creata.
    """
    queryset = Email.objects.select_related("template").prefetch_related("attachments").all()
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        email = self.get_object()
        serializer = EmailSendSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        context_override = serializer.validated_data.get("context_override") or {}
        fail_silently = serializer.validated_data.get("fail_silently", False)

        try:
            ok = send_email(email, context_override=context_override, fail_silently=fail_silently)
        except Exception as e:
            return Response(
                {"detail": f"Errore invio: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        email.refresh_from_db()
        return Response(EmailSerializer(email).data, status=status.HTTP_200_OK)
