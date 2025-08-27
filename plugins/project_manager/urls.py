from django.urls import path
from .views import *

urlpatterns = [
    path('projects/', ProjectList.as_view(), name='project-list'),
    path('projects/<int:pk>/', ProjectDetail.as_view(), name='project-detail'),
    #todo path('projects/<int:project_id>/tutorials/', TutorialList.as_view(), name='project-tutorials'),
    path('project-post/', ProjectView.as_view(), name='project-post'),
    path('project-put/<int:pk>/', ProjectPutView.as_view(), name='project-put'),
    path('projects-from-user/<int:pk>/', ProjectFromUser.as_view(), name='project-from-user'),

]
