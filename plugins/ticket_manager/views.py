from base_modules.attachment.serializers import AttachmentCreateSerializer
from base_modules.mailer.services import send_templated_email
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
from base_modules.user_manager.models import *
import requests
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from .pagination import StandardResultsSetPagination
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone
from django.core.exceptions import ValidationError

class TicketList(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    pagination_class = StandardResultsSetPagination

    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]

    # Ordinamenti consentiti
    allowed_ordering = {
        "id", "-id",
        "opening_date", "-opening_date",
        "closing_date", "-closing_date",
        "priority", "-priority",
    }

    def _parse_date_or_datetime(self, s: str) -> datetime:
        """
        Accetta:
          - 'YYYY-MM-DD' -> restituisce aware datetime alle 00:00
          - ISO 8601 completa -> restituisce aware datetime
        """
        if not s:
            raise ValidationError({"date": "Stringa data vuota"})

        # Prova ISO 8601 completa
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt if timezone.is_aware(dt) else timezone.make_aware(dt)
        except Exception:
            pass

        # Prova solo data 'YYYY-MM-DD'
        try:
            d = datetime.strptime(s, "%Y-%m-%d").date()
            start_dt = datetime.combine(d, time.min)
            return timezone.make_aware(start_dt)
        except Exception:
            raise ValidationError({"date": f"Formato data non valido: {s}"})

    def get_queryset(self):
        user = self.request.user

        qs = (
            Ticket.objects
            .select_related("client", "project", "ticket_workspace")
            .prefetch_related("assignees", "attachments")
        )

        # -----------------------------
        # Permessi/Visibilità
        # -----------------------------
        if hasattr(user, "is_superadmin") and callable(user.is_superadmin) and user.is_superadmin():
            # SuperAdmin: vede tutto
            pass
        elif hasattr(user, "is_associate") and callable(user.is_associate) and user.is_associate():
            # Associate: solo ticket dove è assegnato
            qs = qs.filter(assignees=user)
        else:
            # Utente "normale": visibilità per workspace/client
            workspace_ids = WorkspaceUser.objects.filter(
                user=user
            ).values_list("workspace_id", flat=True)

            users_in_same_ws_ids = WorkspaceUser.objects.filter(
                workspace_id__in=workspace_ids
            ).values_list("user_id", flat=True)

            qs = qs.filter(
                Q(client=user) |
                Q(ticket_workspace_id__in=workspace_ids) |
                Q(client_id__in=users_in_same_ws_ids)
            ).distinct()

        # -----------------------------
        # Filtri Query Params
        # -----------------------------
        params = self.request.query_params

        # status (singolo)
        status_val = params.get("status")
        if status_val:
            qs = qs.filter(status=status_val)

        # status__in (lista CSV)
        status_in_val = params.get("status__in")
        if status_in_val:
            statuses = [s.strip() for s in status_in_val.split(",") if s.strip()]
            if statuses:
                qs = qs.filter(status__in=statuses)

        # assigned: 'true' / 'false'
        assigned = params.get("assigned")
        if assigned == "true":
            qs = qs.filter(assignees__isnull=False)
        elif assigned == "false":
            qs = qs.filter(assignees__isnull=True)

        # priority
        priority = params.get("priority")
        if priority:
            qs = qs.filter(priority=priority)

        # project (ID)
        project = params.get("project")
        if project:
            qs = qs.filter(project_id=project)

        # search (su titolo/descrizione)
        search = params.get("search")
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        # -----------------------------
        # Filtri periodo su opening_date
        # -----------------------------
        year = params.get("year")
        month = params.get("month")
        if year:
            try:
                qs = qs.filter(opening_date__year=int(year))
            except (TypeError, ValueError):
                raise ValidationError({"year": "Anno non valido"})
        if month:
            try:
                m = int(month)
                if m < 1 or m > 12:
                    raise ValidationError({"month": "Mese deve essere 1-12"})
                qs = qs.filter(opening_date__month=m)
            except (TypeError, ValueError):
                raise ValidationError({"month": "Mese non valido"})

        # range from / to
        from_str = params.get("from")
        to_str = params.get("to")

        start_dt: Optional[datetime] = self._parse_date_or_datetime(from_str) if from_str else None
        end_dt: Optional[datetime] = self._parse_date_or_datetime(to_str) if to_str else None

        if start_dt and end_dt and end_dt < start_dt:
            raise ValidationError({"range": "'to' deve essere >= 'from'"})

        if start_dt:
            qs = qs.filter(opening_date__gte=start_dt)
        if end_dt:
            qs = qs.filter(opening_date__lte=end_dt)

        # -----------------------------
        # Ordinamento
        # -----------------------------
        ordering = params.get("ordering")
        if ordering in self.allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-opening_date")

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
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            if ticket:
                send_templated_email(
                    template_slug="notifica_messaggio",
                    to=[ticket.client.email] + [user.email for user in ticket.assignees.all()],
                    context={"user": {"first_name": request.user.first_name}, "ticket": {"id": ticket.id, "title": ticket.title}},
                )
        except Exception as e:
            print("Errore invio email:", str(e))
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
        


class TicketProjectStatsView(APIView):
    """
    GET /api/projects/<project_id>/tickets/stats/?granularity=month|year&from=YYYY-MM-DD&to=YYYY-MM-DD&fill_gaps=true

    Aggrega i ticket del progetto indicato da <project_id> per mese o per anno.
    Breakdown: status, type, priority. Usa opening_date come riferimento.
    """
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get(self, request, project_id: int):
        tz = timezone.get_current_timezone()
        p = request.query_params

        granularity = (p.get("granularity") or "month").lower()
        if granularity not in ("month", "year"):
            return Response({"detail": "granularity deve essere 'month' o 'year'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Base queryset: SOLO il progetto richiesto
        qs = Ticket.objects.filter(project_id=project_id)

        # Date opzionali
        def parse_date(v: str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except Exception:
                return None

        d_from = parse_date(p.get("from") or "")
        d_to = parse_date(p.get("to") or "")

        if d_from:
            qs = qs.filter(opening_date__date__gte=d_from)
        if d_to:
            qs = qs.filter(opening_date__date__lte=d_to)

        trunc = TruncMonth if granularity == "month" else TruncYear

        aggregated = (
            qs.annotate(period=trunc("opening_date", tzinfo=tz))
              .values("period")
              .annotate(
                  total=Count("id"),
                  # status
                  open_=Count("id", filter=Q(status="open")),
                  in_progress=Count("id", filter=Q(status="in_progress")),
                  resolved=Count("id", filter=Q(status="resolved")),
                  closed=Count("id", filter=Q(status="closed")),
                  # type
                  bug=Count("id", filter=Q(ticket_type="bug")),
                  feature=Count("id", filter=Q(ticket_type="feature")),
                  evo=Count("id", filter=Q(ticket_type="evo")),
                  # priority
                  low=Count("id", filter=Q(priority="low")),
                  medium=Count("id", filter=Q(priority="medium")),
                  high=Count("id", filter=Q(priority="high")),
              )
              .order_by("period")
        )

        rows = list(aggregated)
        if not rows and (p.get("fill_gaps") or "").lower() == "true":
            return Response({
                "project_id": project_id,
                "granularity": granularity,
                "date_range": {"start": d_from.isoformat() if d_from else None,
                               "end": d_to.isoformat() if d_to else None},
                "results": []
            })

        # Mappa periodo -> dati
        data_by_key = {}
        for r in rows:
            per = r["period"]
            if granularity == "month":
                key = per.strftime("%Y-%m")
                per_start = date(per.year, per.month, 1)
            else:
                key = per.strftime("%Y")
                per_start = date(per.year, 1, 1)
            data_by_key[key] = {
                "period": key,
                "period_start": per_start.isoformat(),
                "total": r["total"],
                "by_status": {
                    "open": r["open_"],
                    "in_progress": r["in_progress"],
                    "resolved": r["resolved"],
                    "closed": r["closed"],
                },
                "by_type": {"bug": r["bug"], "feature": r["feature"], "evo": r["evo"]},
                "by_priority": {"low": r["low"], "medium": r["medium"], "high": r["high"]},
            }

        # Gap filling opzionale
        results = []
        fill_gaps = (p.get("fill_gaps") or "").lower() == "true"
        if fill_gaps and data_by_key:
            # start
            if d_from:
                start = d_from
            else:
                first_key = sorted(data_by_key.keys())[0]
                first_dt = datetime.strptime(first_key, "%Y-%m" if granularity == "month" else "%Y").date()
                start = date(first_dt.year, first_dt.month if granularity == "month" else 1, 1)
            # end
            if d_to:
                end = d_to
            else:
                last_key = sorted(data_by_key.keys())[-1]
                last_dt = datetime.strptime(last_key, "%Y-%m" if granularity == "month" else "%Y").date()
                end = date(last_dt.year, last_dt.month if granularity == "month" else 12, 1)

            cur = start.replace(day=1)
            while cur <= end:
                if granularity == "month":
                    key = cur.strftime("%Y-%m")
                    per_start = date(cur.year, cur.month, 1)
                    cur = per_start + relativedelta(months=1)
                else:
                    key = cur.strftime("%Y")
                    per_start = date(cur.year, 1, 1)
                    cur = date(cur.year + 1, 1, 1)

                results.append(data_by_key.get(key, {
                    "period": key,
                    "period_start": per_start.isoformat(),
                    "total": 0,
                    "by_status": {"open": 0, "in_progress": 0, "resolved": 0, "closed": 0},
                    "by_type": {"bug": 0, "feature": 0, "evo": 0},
                    "by_priority": {"low": 0, "medium": 0, "high": 0},
                }))
        else:
            results = [data_by_key[k] for k in sorted(data_by_key.keys())]

        return Response({
            "project_id": project_id,
            "granularity": granularity,
            "date_range": {
                "start": d_from.isoformat() if d_from else (results[0]["period_start"] if results else None),
                "end": d_to.isoformat() if d_to else (results[-1]["period_start"] if results else None),
            },
            "results": results
        }, status=status.HTTP_200_OK)