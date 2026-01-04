from rest_framework import generics

from mixtum_core.settings.base import REMOTE_API
from .models import Subscription
from .serializers import SubscriptionSerializer, SubscriptionSerializerAdd
from base_modules.user_manager.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q
from plugins.project_manager.models import Project
from plugins.project_manager.permissions import requester_shares_workspace_with_project_client


def _accessible_project_ids_for(user):
    from base_modules.user_manager.models import User

    if user.permission in (100, 50):
        return set(Project.objects.values_list('id', flat=True))

    ids = set()
    if user.permission == 1:
        ids.update(Project.objects.filter(client=user).values_list('id', flat=True))

    for project in Project.objects.exclude(id__in=ids):
        if requester_shares_workspace_with_project_client(project.id, user.id):
            ids.add(project.id)

    return ids

class SubscriptionList(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Subscription.objects.all()

    def get(self, request):
        # Controllo sull'utente
        if request.user.is_at_least_associate():
            subscriptions = Subscription.objects.all()
        else:
            accessible_project_ids = _accessible_project_ids_for(request.user)
            if accessible_project_ids:
                subscriptions = Subscription.objects.filter(
                    Q(customer=request.user) |
                    Q(project__id__in=accessible_project_ids)

                ).distinct()
            else:
                subscriptions = Subscription.objects.filter(customer=request.user)

        subscriptions_serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response({'data': subscriptions_serializer.data}, status=status.HTTP_200_OK)



class SubscriptionDetail(generics.GenericAPIView):
    serializer_class = SubscriptionSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT']:  # Usa il serializer specifico per POST e PUT
            return SubscriptionSerializerAdd
        return SubscriptionSerializer

    def get(self, request, pk):
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({"message": "subscription not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_at_least_associate():
            serializer = self.get_serializer(subscription)
            return Response({'data': serializer.data, "message": "success"}, status=status.HTTP_200_OK)

        accessible_project_ids = _accessible_project_ids_for(request.user)
        if (
            subscription.customer_id == request.user.id or
            (accessible_project_ids and subscription.project.filter(id__in=accessible_project_ids).exists())
        ):
            serializer = self.get_serializer(subscription)
            return Response({'data': serializer.data, "message": "success"}, status=status.HTTP_200_OK)

        return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            subscription = serializer.save()
            return Response({'data': SubscriptionSerializer(subscription).data, "message": "success"}, status=status.HTTP_201_CREATED)
        return Response({"data": serializer.errors, "message": "fail"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            subscription = None

        if request.user.is_authenticated:  # Puoi cambiare il controllo dei permessi se necessario
            if subscription:
                serializer = self.get_serializer(instance=subscription, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
                return Response({"data": serializer.errors, "message": "fail"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "subscription not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


