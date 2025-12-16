from .views import *
from django.urls import path


urlpatterns = [
    path('reports/', AllReportAPIView.as_view(), name='report-list'),
    path('reports/project/<int:project>/', ProjectReportListAPIView.as_view(), name='project-report-list'),
    path('reports/<int:pk>/', ReportDetailAPIView.as_view(), name='report-detail'),
    path('reports-by-ticket/', ReportByTicketAPIView.as_view(), name='report-by-ticket'),
]
