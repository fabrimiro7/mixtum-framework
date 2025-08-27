# workspace/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkspaceViewSet, WorkspaceUserViewSet, UserViewSet

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'workspace-users', WorkspaceUserViewSet, basename='workspaceuser')
router.register(r'users', UserViewSet, basename='user') 

urlpatterns = [
    path('', include(router.urls)),
]


