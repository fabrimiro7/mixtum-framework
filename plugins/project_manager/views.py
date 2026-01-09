from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from django.db.models import Q
from .models import Project
from .serializers import ProjectSerializer, ProjectSerializerGet
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication

from plugins.project_manager.permissions import requester_shares_workspace_with_project_client


def _accessible_project_ids_for(user):
    if user.is_superadmin() or user.is_admin():
        return set(Project.objects.values_list('id', flat=True))

    ids = set(Project.objects.filter(client=user).values_list('id', flat=True))
    for project in Project.objects.exclude(id__in=ids):
        if requester_shares_workspace_with_project_client(project.id, user.id):
            ids.add(project.id)
    return ids


class ProjectList(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Project.objects.all()

    def get(self, request):
        if request.user.is_superadmin() or request.user.is_admin():
            projects = Project.objects.all()
        else:
            accessible_project_ids = _accessible_project_ids_for(request.user)
            if accessible_project_ids:
                projects = Project.objects.filter(id__in=accessible_project_ids)
            else:
                projects = Project.objects.filter(client=request.user)
        projects_serializer = ProjectSerializerGet(projects, many=True)
        return Response({'data': projects_serializer.data}, status=status.HTTP_200_OK)


class ProjectDetail(generics.RetrieveUpdateAPIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get(self, request, pk):
        if request.user.is_at_least_associate():
            try:
                project = Project.objects.get(pk=pk)
            except Exception:
                project = None
            if project:
                serializer = ProjectSerializerGet(project)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            accessible_project_ids = _accessible_project_ids_for(request.user)
            if pk in accessible_project_ids:
                project = Project.objects.get(pk=pk)
                serializer = ProjectSerializerGet(project)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    def delete(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Exception:
            project = None
        if request.user.is_at_least_associate():
            if project:
                project.delete()
                return Response({"message": "success"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    
class ProjectPutView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = ProjectSerializer

    def put(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Exception:
            project = None
        if request.user.is_at_least_associate():
            if project:
                serializer = ProjectSerializer(project, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
                return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


class ProjectView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = ProjectSerializer

    def post(self, request, *args, **kwargs):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            tutorial = serializer.save()
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
        return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)


class ProjectFromUser(generics.RetrieveUpdateAPIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get(self, request, pk):
        try:
            if request.user.permission == 100:
                projects = Project.objects.all()
            else:
                projects = Project.objects.filter(
                    Q(client=pk) | Q(contributors=pk)
                ).distinct()
        except Exception:
            projects = None
        if projects:
            serializer = ProjectSerializer(projects, many=True)
            return Response({"data": serializer.data, "message":"success"}, status=status.HTTP_200_OK)
        else:
            return Response({"data": [], "message": "fail"}, status=status.HTTP_200_OK)
       
