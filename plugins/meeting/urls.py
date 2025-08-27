from .views import *
from django.urls import path


urlpatterns = [
    path('meetings/', MeetingList.as_view(), name='meeting-list'),
    path('meetings/<int:pk>/', MeetingDetail.as_view(), name='meeting-detail'),
    path('meeting-post/', MeetingView.as_view(), name='meeting-post'),
    path('meeting-put/<int:pk>/', MeetingPutView.as_view(), name='meeting-put'),
]