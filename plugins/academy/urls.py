from django.urls import path
from .views import *

urlpatterns = [
    #todo path('academy/<int:project_id>/tutorials/', TutorialList.as_view(), name='project-tutorials'),
    path('tutorial/', TutorialList.as_view(), name='tutorial-list'),
    path('tutorial-by-project/<int:pk>/', TutorialByProjectView.as_view(), name='tutorial-by-project'),
    path('tutorial-detail/<int:pk>/', TutorialDetail.as_view(), name='tutorial-detail'),
    path('tutorial-put/<int:pk>/', TutorialPutView.as_view(), name='tutorial-put'),
    path('tutorial-post/', TutorialView.as_view(), name='tutorial-post'),
    path('notes/', NoteListCreateView.as_view(), name='note-list-create'),
    path('notes/<int:pk>/', NoteDetailView.as_view(), name='note-detail'),
    path('notes/by-tutorial/<int:tutorial_id>/', NoteByTutorialView.as_view(), name='note-by-tutorial'),
    path('notes/add/', AddNoteView.as_view(), name='note-add'),
    path('categories/', CategoryViewSet.as_view({'get': 'list'}), name='category-list'),
    path('category/<int:pk>/', CategoryViewSet.as_view({'get': 'retrieve'}), name='category-detail'),
    path('category-create/', CategoryViewSet.as_view({'post': 'create'}), name='category-create'),
    path('category-update/<int:pk>/', CategoryViewSet.as_view({'put': 'update'}), name='category-update'),
    path('category-delete/<int:pk>/', CategoryViewSet.as_view({'delete': 'destroy'}), name='category-delete'),
    ]
