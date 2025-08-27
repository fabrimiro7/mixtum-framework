from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from .models import Project
from .serializers import ProjectSerializer, ProjectSerializerGet
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication


class ProjectList(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Project.objects.all()

    def get(self, request):
        if request.user.is_superadmin():
            projects = Project.objects.all()
        else:
            projects = Project.objects.filter(client=request.user)
        projects_serializer = ProjectSerializerGet(projects, many=True)
        return Response({'data': projects_serializer.data}, status=status.HTTP_200_OK)


#class ProjectDetail(generics.RetrieveUpdateAPIView):
#    if REMOTE_API == True:
#        authentication_classes = [JWTAuthentication]
#    queryset = Project.objects.all()
#    serializer_class = ProjectSerializer

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
            project = Project.objects.get(pk=pk, client=request.user)
            if project:
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
                projects = Project.objects.filter(client=pk)
        except Exception:
            projects = None
        if projects:
            serializer = ProjectSerializer(projects, many=True)
            return Response({"data": serializer.data, "message":"success"}, status=status.HTTP_200_OK)
        else:
            return Response({"data": [], "message": "fail"}, status=status.HTTP_200_OK)
       
