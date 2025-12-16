from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Report
from .serializers import ReportSerializer

ROLE_LABELS = {
    100: 'SuperAdmin',
    50: 'Admin',
    10: 'Utente',
    5: 'Employee',
    1: 'Utente',
}


def _get_role_label(user):
    permission_value = getattr(user, 'permission', None)
    return ROLE_LABELS.get(permission_value, 'Utente')


def _filter_queryset_by_role(queryset, user):
    if not user or not getattr(user, 'is_authenticated', False):
        return queryset.none()
    if user.is_at_least_associate():
        return queryset
    role_label = _get_role_label(user)
    return queryset.filter(visible_roles__contains=[role_label])


def _user_can_view_report(user, report):
    if not user or not getattr(user, 'is_authenticated', False) or not report:
        return False
    if user.is_at_least_associate():
        return True
    if report.report_ticket and report.report_ticket.client == user:
        return True
    role_label = _get_role_label(user)
    visible_roles = report.visible_roles or []
    return role_label in visible_roles


def _user_can_modify_report(user, report):
    if not user or not getattr(user, 'is_authenticated', False) or not report:
        return False
    if user.is_at_least_associate():
        return True
    return report.report_ticket and report.report_ticket.client == user


class AllReportAPIView(APIView):
    serializer_class = ReportSerializer

    def get(self, request):
        if not request.user.is_at_least_associate():
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportSerializer(Report.objects.all(), many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if not request.user.is_at_least_associate():
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_201_CREATED)


class ProjectReportListAPIView(APIView):
    serializer_class = ReportSerializer

    def get(self, request, project):
        reports = Report.objects.filter(report_project_id=project)
        reports = _filter_queryset_by_role(reports, request.user)
        serializer = ReportSerializer(reports, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


class ReportDetailAPIView(APIView):
    serializer_class = ReportSerializer

    def get(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        if not _user_can_view_report(request.user, report):
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportSerializer(report)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        if not _user_can_modify_report(request.user, report):
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)
        report.delete()
        return Response({"message": "success"}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        if not _user_can_modify_report(request.user, report):
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportSerializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)


class ReportByTicketAPIView(APIView):
    serializer_class = ReportSerializer

    def get(self, request, ticket):
        report = Report.objects.filter(report_ticket_id=ticket).first()
        if not report:
            return Response({"message": "fail, report non trovato"}, status=status.HTTP_404_NOT_FOUND)
        if not _user_can_view_report(request.user, report):
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportSerializer(report)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, ticket):
        report = Report.objects.filter(report_ticket_id=ticket).first()
        if not report:
            return Response({"message": "fail"}, status=status.HTTP_404_NOT_FOUND)
        if not _user_can_modify_report(request.user, report):
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)
        report.delete()
        return Response({"message": "success"}, status=status.HTTP_200_OK)

    def put(self, request, ticket):
        report = Report.objects.filter(report_ticket_id=ticket).first()
        if not report:
            return Response({"message": "fail"}, status=status.HTTP_404_NOT_FOUND)
        if not _user_can_modify_report(request.user, report):
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportSerializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
