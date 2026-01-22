from django.urls import path
from .views import *

urlpatterns = [
    path('tickets/', TicketList.as_view(), name='ticket-list'),
    path('tickets-add/', TicketView.as_view(), name='ticket-add'),
    path('tickets/<int:pk>/', TicketDetail.as_view(), name='ticket-detail'),
    path('tickets-put/<int:pk>/', TicketPutView.as_view(), name='ticket-put'),
    path('tickets-all/', TicketView.as_view(), name='all-ticket-list'),
    path('tickets/<int:ticket_id>/messages/', TicketMessages.as_view(), name='ticket-messages'),
    path('tickets/<int:ticket_id>/mark-as-read/', MarkTicketAsRead.as_view(), name='ticket-mark-as-read'),
    path('my-assigned-tickets/', UserAssignedTicketList.as_view(), name='user-assigned-tickets'),
    path('my-client-tickets/', UserClientTicketList.as_view(), name='user-client-tickets'),

    path('ticket-payments-toggle/<int:pk>/', ToggleTicketPayment.as_view(), name='ticket-payments-toggle'),

    path('attachment-tickets/<int:ticket_id>/', TicketAttachment.as_view(), name='attachment-tickets'),
    path('attachment-message/<int:message_id>/', TicketMessageAttachment.as_view(), name='attachment-message'),

    path('monthly-tickets/<int:project_id>/', TicketProjectStatsView.as_view(), name='monthly-tickets'),
    path('tasks/', ProjectTaskList.as_view(), name='project-tasks'),
    path('tasks/<int:pk>/', TaskUpdateView.as_view(), name='task-update'),
]
