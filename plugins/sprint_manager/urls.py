from django.urls import path
from .views import ProjectPhaseList, PhaseDetail, AllPhaseList

app_name = 'sprint_manager'

urlpatterns = [
    path('phases/', ProjectPhaseList.as_view(), name='phase-list'),
    path('phases/<int:pk>/', PhaseDetail.as_view(), name='phase-detail'),
    path('phases/all/', AllPhaseList.as_view(), name='phase-all'),
]
