from django.shortcuts import render

from .models import *
from base_modules.user_manager.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework import status, generics
from mixtum_core.settings.base import REMOTE_API
from .serializers import *
from rest_framework.views import APIView


class AttachmentCreateView(generics.CreateAPIView):
    
    serializer_class = AttachmentEditSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.validated_data['author'] = request.user
            serializer.save()
            attachment_data = serializer.data
            return Response({
                "Attachment": attachment_data,
                "message": "success",
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AttachmentDeleteView(generics.DestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "success"}, status=status.HTTP_204_NO_CONTENT)

class AttachmentUpdateView(generics.UpdateAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentEditSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        return Response({
            "Attachment": serializer.data,
            "message": "success",
        }, status=status.HTTP_200_OK)

class AttachmentListView(generics.ListAPIView):
    serializer_class = AttachmentSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        return Attachment.objects.filter(author=user)
    
class AttachmentDetailView(generics.RetrieveAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)