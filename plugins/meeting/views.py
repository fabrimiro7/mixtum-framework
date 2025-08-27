from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from .models import Meeting
from .serializers import MeetingSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication
from django.db.models import Q


class MeetingList(generics.ListCreateAPIView):
    serializer_class = MeetingSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Meeting.objects.all()

    def get(self, request):
        if request.user.is_superadmin():
            meetings = Meeting.objects.all()
        else:
            meetings = Meeting.objects.filter(Q(insert_by__id=request.user.id) | Q(client__id=request.user.id))
        meetings_serializer = MeetingSerializer(meetings, many=True)
        return Response({'data': meetings_serializer.data}, status=status.HTTP_200_OK)




class MeetingDetail(generics.RetrieveUpdateAPIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]
    serializer_class = MeetingSerializer

    def get(self, request, pk):
        if request.user.is_superadmin():
            meeting = Meeting.objects.filter(pk=pk)
        else:
            try:
                meeting = Meeting.objects.filter((Q(insert_by__id=request.user.id) | Q(client__id=request.user.id)), pk=pk)
            except Exception as e:
                print(e)
                return Response({'data': ''}, status=status.HTTP_200_OK)
        meetings_serializer = MeetingSerializer(meeting)
        return Response({'data': meetings_serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            meeting = Meeting.objects.get(pk=pk)
        except Exception:
            meeting = None
        if request.user.is_at_least_associate():
            if meeting:
                meeting.delete()
                return Response({"message": "success"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

class MeetingPutView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = MeetingSerializer

    def get(self, request, pk):
        try:
            meeting = Meeting.objects.get(pk=pk)
        except Exception:
            meeting = None
        if request.user.is_at_least_associate():
            if meeting:
                serializer = MeetingSerializer(meeting)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "fail, meeting non trovato"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    def put(self, request, pk):
        try:
            meeting = Meeting.objects.get(pk=pk)
        except Exception:
            meeting = None
        if request.user.is_at_least_associate():
            if meeting:
                serializer = MeetingSerializer(meeting, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
                return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


class MeetingView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = MeetingSerializer

    def post(self, request, *args, **kwargs):
        serializer = MeetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            tutorial = serializer.save()
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
        return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)