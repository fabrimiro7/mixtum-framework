from django.urls import path
from base_modules.attachment.views import *

urlpatterns = [
    path('create/', AttachmentCreateView.as_view(), name='attachment-create'),
    path('update/<int:pk>/', AttachmentUpdateView.as_view(), name='attachment-update'),
    path('delete/<int:pk>/', AttachmentDeleteView.as_view(), name='attachment-delete'),
    path('list/', AttachmentListView.as_view(), name='attachment-list'),
    path('details/<int:pk>/', AttachmentDetailView.as_view(), name='attachment-details'),
]