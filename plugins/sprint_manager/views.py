from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from base_modules.user_manager.authentication import JWTAuthentication
from plugins.project_manager.models import Project
from .models import Phase, TASK_STATUS_CHOICES
from .serializers import PhaseSerializer, PhaseCreateSerializer


class ProjectPhaseList(APIView):
    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project')
        if not project_id:
            return Response({"detail": "Parametro 'project' obbligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({"detail": "Progetto non trovato."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if hasattr(user, "is_at_least_associate") and callable(user.is_at_least_associate) and user.is_at_least_associate():
            pass
        elif project.client_id == getattr(user, "id", None):
            pass
        else:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        phases = Phase.objects.filter(project=project).select_related('owner')
        serializer = PhaseSerializer(phases, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        project_id = request.data.get('project') or request.data.get('project_id')
        if not project_id:
            return Response(
                {"detail": "Parametro 'project' o 'project_id' obbligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({"detail": "Progetto non trovato."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if hasattr(user, "is_at_least_associate") and callable(user.is_at_least_associate) and user.is_at_least_associate():
            pass
        elif project.client_id == getattr(user, "id", None):
            pass
        else:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        data = dict(request.data)
        if 'project_id' in data and 'project' not in data:
            data['project'] = data.pop('project_id')
        elif 'project' not in data:
            data['project'] = project_id

        serializer = PhaseCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phase = serializer.save()
        out = PhaseSerializer(phase)
        return Response(out.data, status=status.HTTP_201_CREATED)


class PhaseDetail(APIView):
    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        phase = get_object_or_404(Phase.objects.select_related('project', 'project__client'), pk=pk)

        user = request.user
        if hasattr(user, "is_at_least_associate") and callable(user.is_at_least_associate) and user.is_at_least_associate():
            pass
        elif phase.project.client_id == getattr(user, "id", None):
            pass
        elif phase.owner_id == getattr(user, "id", None):
            pass
        else:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        updates = {}
        new_status = request.data.get('status')
        new_start = request.data.get('start_date')
        new_due = request.data.get('due_date')

        if new_status is None and new_start is None and new_due is None:
            return Response({"detail": "Nessun campo valido fornito."}, status=status.HTTP_400_BAD_REQUEST)

        if new_status is not None:
            valid_status = {choice[0] for choice in TASK_STATUS_CHOICES}
            if new_status not in valid_status:
                return Response({"detail": "Status non valido."}, status=status.HTTP_400_BAD_REQUEST)
            updates['status'] = new_status

        from datetime import datetime

        def parse_date(value, field_name):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except Exception:
                raise ValueError(f"Formato data non valido per {field_name}.")

        if new_start is not None:
            try:
                updates['start_date'] = parse_date(new_start, 'start_date')
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if new_due is not None:
            try:
                updates['due_date'] = parse_date(new_due, 'due_date')
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if 'start_date' in updates and 'due_date' in updates:
            if updates['due_date'] < updates['start_date']:
                return Response({"detail": "La data di fine non può precedere la data di inizio."}, status=status.HTTP_400_BAD_REQUEST)
        elif 'start_date' in updates and phase.due_date and phase.due_date < updates['start_date']:
            return Response({"detail": "La data di fine non può precedere la data di inizio."}, status=status.HTTP_400_BAD_REQUEST)
        elif 'due_date' in updates and phase.start_date and updates['due_date'] < phase.start_date:
            return Response({"detail": "La data di fine non può precedere la data di inizio."}, status=status.HTTP_400_BAD_REQUEST)

        for field, value in updates.items():
            setattr(phase, field, value)

        update_fields = list(updates.keys()) + ['updated_at']
        phase.save(update_fields=update_fields)
        serializer = PhaseSerializer(phase)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AllPhaseList(APIView):
    if JWTAuthentication is not None:
        authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (hasattr(user, "is_at_least_associate") and callable(user.is_at_least_associate) and user.is_at_least_associate()):
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        phases = Phase.objects.all().select_related('owner', 'project')
        serializer = PhaseSerializer(phases, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
