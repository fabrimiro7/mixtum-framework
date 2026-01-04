from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from plugins.project_manager.models import Project
from plugins.project_manager.permissions import requester_shares_workspace_with_project_client

from .models import Report
from .serializers import ReportSerializer


def _resolve_report_project_id(report: Report):
    if report.report_project_id:
        return report.report_project_id
    ticket = getattr(report, 'report_ticket', None)
    return getattr(ticket, 'project_id', None) if ticket else None


def _user_can_view_report(user, report):
    if not user or not getattr(user, 'is_authenticated', False) or not report:
        return False
    if user.is_at_least_associate():
        return True
    if report.report_ticket and report.report_ticket.client_id == user.id:
        return True
    if report.report_project and report.report_project.client_id == user.id:
        return True
    project_id = _resolve_report_project_id(report)
    if project_id and requester_shares_workspace_with_project_client(project_id, user.id):
        return True
    return False


def _user_can_modify_report(user, report):
    if not user or not getattr(user, 'is_authenticated', False) or not report:
        return False
    if user.is_at_least_associate():
        return True
    return report.report_ticket and report.report_ticket.client_id == user.id


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
        user = request.user
        if not getattr(user, 'is_authenticated', False):
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

        project_obj = get_object_or_404(Project, pk=project)
        if not user.is_at_least_associate():
            if project_obj.client_id != user.id and not requester_shares_workspace_with_project_client(project_obj.id, user.id):
                return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

        reports = Report.objects.filter(report_project_id=project_obj.id)
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
