from django.shortcuts import render
from rest_framework import generics
from rest_framework import status
from django.http import HttpResponse
from rest_framework.response import Response
from .models import Report
from .serializers import ReportSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication
from django.db.models import Q
from base_modules.user_manager.models import *




class AllReportAPIView(APIView):
    serializer_class = ReportSerializer

    def get(self, request):
        if request.user.is_at_least_associate():
            try:
                all_report = Report.objects.all()
            except Exception:
                all_report = None
            if all_report:
                serializer = ReportSerializer(all_report, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)



    def post(self, request, *args, **kwargs):
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            report = serializer.save()
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
        return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)


class ReportDetailAPIView(APIView):
    serializer_class = ReportSerializer
    queryset = ''

    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Exception:
            report = None
        if request.user.is_at_least_associate() or report.report_ticket.client == request.user:
            if report:
                serializer = ReportSerializer(report)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "fail, report non trovato"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    def delete(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Exception:
            report = None
        if request.user.is_at_least_associate() or report.report_ticket.client == request.user:
            if report:
                report.delete()
                return Response({"message": "success"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Exception:
            report = None
        if request.user.is_at_least_associate() or report.report_ticket.client == request.user:
            if report:
                serializer = ReportSerializer(report)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
                return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


class ReportByTicketAPIView(APIView):
    serializer_class = ReportSerializer
    queryset = ''

    def get(self, request, ticket):
        try:
            report = Report.objects.get(report_ticket=ticket)
        except Exception:
            report = None
        if request.user.is_at_least_associate() or ticket.client == request.user:
            if report:
                serializer = ReportSerializer(report)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "fail, report non trovato"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    def delete(self, request, ticket):
        try:
            report = Report.objects.get(report_ticket=ticket)
        except Exception:
            report = None
        if request.user.is_at_least_associate() or ticket.client == request.user:
            if report:
                report.delete()
                return Response({"message": "success"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, ticket):
        try:
            report = Report.objects.get(report_ticket=ticket)
        except Exception:
            report = None
        if request.user.is_at_least_associate() or ticket.client == request.user:
            if report:
                serializer = ReportSerializer(report)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
                return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)