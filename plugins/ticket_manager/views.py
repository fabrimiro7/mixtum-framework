from base_modules.attachment.serializers import AttachmentCreateSerializer
from base_modules.workspace.models import WorkspaceUser
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from .models import Ticket, Message
from base_modules.user_manager.models import User
from .serializers import MessageFullSerializer, TicketSerializer, MessageSerializer, TicketPostSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication
from django.db.models import Q
from base_modules.user_manager.models import *
import requests
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from .pagination import StandardResultsSetPagination

class TicketList(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user

        qs = (Ticket.objects
              .select_related('client', 'project', 'ticket_workspace')
              .prefetch_related('assignees', 'attachments'))

        if hasattr(user, 'is_superadmin') and user.is_superadmin():
            pass  
        elif hasattr(user, 'is_associate') and user.is_associate():
            qs = qs.filter(assignees=user)
        else:
            workspace_ids = WorkspaceUser.objects.filter(
                user=user
            ).values_list('workspace_id', flat=True)

            users_in_same_ws_ids = WorkspaceUser.objects.filter(
                workspace_id__in=workspace_ids
            ).values_list('user_id', flat=True)

            qs = qs.filter(
                Q(client=user) |
                Q(ticket_workspace_id__in=workspace_ids) |
                Q(client_id__in=users_in_same_ws_ids)
            ).distinct()

        params = self.request.query_params

        status_val = params.get('status')
        if status_val:
            qs = qs.filter(status=status_val)

        status_in_val = params.get('status__in')
        if status_in_val:
            statuses = [s.strip() for s in status_in_val.split(',') if s.strip()]
            if statuses:
                qs = qs.filter(status__in=statuses)

        assigned = params.get('assigned')
        if assigned == 'true':
            qs = qs.filter(assignees__isnull=False)
        elif assigned == 'false':
            qs = qs.filter(assignees__isnull=True)

        priority = params.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        project = params.get('project')
        if project:
            qs = qs.filter(project_id=project)

        search = params.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        ordering = params.get('ordering')
        allowed_ordering = {'id', '-id', 'opening_date', '-opening_date', 'closing_date', '-closing_date', 'priority', '-priority'}
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by('-opening_date')

        return qs


class TicketDetail(generics.RetrieveUpdateAPIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Exception:
            ticket = None
        if request.user.is_at_least_associate() or ticket.client == request.user:
            if ticket:
                serializer = TicketSerializer(ticket)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "fail, ticket non trovato"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    def delete(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Exception:
            ticket = None
        if request.user.is_at_least_associate() or ticket.client == request.user:
            if ticket:
                ticket.delete()
                return Response({"message": "success"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

class TicketPutView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = TicketPostSerializer

    def get(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Exception:
            ticket = None
        if request.user.is_at_least_associate() or ticket.client == request.user:
            if ticket:
                serializer = TicketPostSerializer(ticket)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "fail, ticket non trovato"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    def put(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Exception:
            ticket = None
        if request.user.is_at_least_associate() or ticket.client == request.user:
            if ticket:
                serializer = TicketPostSerializer(ticket, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
                error_list = [serializer.errors[error][0] for error in serializer.errors]
                print(error_list)
                return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


class TicketView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = TicketPostSerializer

    def get(self, request):
        user = request.user
        if user.is_superadmin():
            not_assigned_ticket = Ticket.objects.filter(assignees=None, status="open")
            assigned_ticket = Ticket.objects.filter(Q(status="open")| Q (status="in_progress")).exclude(assignees=None)
            resolved_ticket = Ticket.objects.filter(Q(status="resolved")| Q (status="closed")).exclude(assignees=None)
            nat = TicketPostSerializer(not_assigned_ticket, many=True)
            at = TicketPostSerializer(assigned_ticket, many=True)
            rt = TicketPostSerializer(resolved_ticket, many=True)
            data = {
                'not_assigned_ticket': nat.data,
                'assigned_ticket': at.data,
                'resolved_ticket': rt.data,
            }
            return Response(data, status=status.HTTP_200_OK)
        elif user.is_at_least_associate():
            assigned_ticket = Ticket.objects.filter(Q(status="open") | Q(status="in_progress")).exclude(assignees=None)
            resolved_ticket = Ticket.objects.filter(Q(status="resolved") | Q(status="closed")).exclude(assignees=None)
            at = TicketPostSerializer(assigned_ticket, many=True)
            rt = TicketPostSerializer(resolved_ticket, many=True)
            data = {
                'assigned_ticket': at.data,
                'resolved_ticket': rt.data,
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            open_ticket = Ticket.objects.filter(client=user,status="open")
            in_progress_ticket = Ticket.objects.filter(client=user,status="in_progress")
            resolved_ticket = Ticket.objects.filter((Q(status="resolved")|Q(status="closed")),client=user)
            ot = TicketPostSerializer(open_ticket, many=True)
            it = TicketPostSerializer(in_progress_ticket, many=True)
            rt = TicketPostSerializer(resolved_ticket, many=True)
            data = {
                'open_ticket': ot.data,
                'in_progress_ticket': it.data,
                'resolved_ticket': rt.data,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request, *args, **kwargs):
        serializer = TicketPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            ticket = serializer.save()
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
        return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)

class UserAssignedTicketList(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        in_progress_tickets = Ticket.objects.filter(assignees=user, status='in_progress')
        open_tickets = Ticket.objects.filter(assignees=user, status='open')
        resolved_tickets = Ticket.objects.filter(assignees=user, status='resolved')
        closed_tickets = Ticket.objects.filter(assignees=user, status='closed')

        in_progress_serializer = TicketSerializer(in_progress_tickets, many=True)
        open_serializer = TicketSerializer(open_tickets, many=True)
        resolved_serializer = TicketSerializer(resolved_tickets, many=True)
        closed_serializer = TicketSerializer(closed_tickets, many=True)

        return Response({
            'in_progress': in_progress_serializer.data,
            'open': open_serializer.data,
            'resolved': resolved_serializer.data,
            'closed': closed_serializer.data,
        }, status=status.HTTP_200_OK)


class UserClientTicketList(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        in_progress_tickets = Ticket.objects.filter(client=user, status='in_progress')
        open_tickets = Ticket.objects.filter(client=user, status='open')
        resolved_tickets = Ticket.objects.filter(client=user, status='resolved')
        closed_tickets = Ticket.objects.filter(client=user, status='closed')

        in_progress_serializer = TicketSerializer(in_progress_tickets, many=True)
        open_serializer = TicketSerializer(open_tickets, many=True)
        resolved_serializer = TicketSerializer(resolved_tickets, many=True)
        closed_serializer = TicketSerializer(closed_tickets, many=True)

        return Response({
            'in_progress': in_progress_serializer.data,
            'open': open_serializer.data,
            'resolved': resolved_serializer.data,
            'closed': closed_serializer.data,
        }, status=status.HTTP_200_OK)


class TicketMessages(generics.ListCreateAPIView):
    serializer_class = MessageFullSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get(self, request, ticket_id):
        messages = Message.objects.filter(ticket__id=ticket_id)
        if messages:
            messages_serializer = MessageFullSerializer(messages, many=True)
            return Response({"data": messages_serializer.data, "message":"success"}, status=status.HTTP_200_OK)
        return Response({"data": [], "message":"fail"}, status=status.HTTP_200_OK)
    
    def post(self, request, ticket_id):
        request_data = request.data.copy()
        request_data['ticket'] = ticket_id
        request_data['author'] = request.user.id
        message_serializer = MessageSerializer(data=request_data)
        if message_serializer.is_valid():
            message_serializer.save()
            return Response({"data": message_serializer.data, "message": "success"}, status=status.HTTP_201_CREATED)
        return Response({"data": message_serializer.errors, "message": "fail"}, status=status.HTTP_400_BAD_REQUEST)



class TicketAttachment(APIView):
    serializer_class = AttachmentCreateSerializer
    parser_classes = (MultiPartParser, FormParser)  # Assicurati di avere i parser corretti

    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def post(self, request, ticket_id):
        print("ticket_id", ticket_id)
        ticket = get_object_or_404(Ticket, id=ticket_id)
        
        try:
            serializer = self.serializer_class(data=request.data)
            
            if serializer.is_valid():
                attachment = serializer.save(author=request.user)
                ticket.attachments.add(attachment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print("sono qui")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        

'''
Messages API
'''

class TicketMessageAttachment(APIView):
    serializer_class = AttachmentCreateSerializer
    parser_classes = (MultiPartParser, FormParser)  # Assicurati di avere i parser corretti

    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        
        try:
            serializer = self.serializer_class(data=request.data)
            
            if serializer.is_valid():
                attachment = serializer.save(author=request.user)
                message.attachments.add(attachment)
                return Response({"data":serializer.data, "message":"success"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"data":serializer.errors, "message":"fail"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"detail": str(e), "message":"fail"}, status=status.HTTP_400_BAD_REQUEST)