from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from plugins.project_manager.models import Project
from .models import Tutorial, Note, Category
from .serializers import TutorialFullSerializer, TutorialSerializer, NoteSerializer, CategorySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from rest_framework import viewsets

from plugins.project_manager.permissions import requester_shares_workspace_with_project_client


def _accessible_project_ids_for(user):
    if user.permission in (100, 50):
        return set(Project.objects.values_list('id', flat=True))

    ids = set()
    if user.permission == 1:
        ids.update(Project.objects.filter(client=user).values_list('id', flat=True))

    for project in Project.objects.exclude(id__in=ids):
        if requester_shares_workspace_with_project_client(project.id, user.id):
            ids.add(project.id)

    return ids



class TutorialList(generics.ListCreateAPIView):
    serializer_class = TutorialFullSerializer
    if REMOTE_API:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user

        if user.permission in (100, 50):
            return Tutorial.objects.all().distinct()

        accessible_project_ids = _accessible_project_ids_for(user)
        if not accessible_project_ids:
            return Tutorial.objects.none()

        return Tutorial.objects.filter(projects__id__in=accessible_project_ids).distinct()

class TutorialByProjectView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = TutorialSerializer
    def get(self, request, pk): ###pk è l'id del progetto per cui effettuiamo la ricerca
        tutorials = Tutorial.objects.filter(projects__id=pk)
        tutorials_serializer = TutorialFullSerializer(tutorials, many=True)
        return Response({'data': tutorials_serializer.data}, status=status.HTTP_200_OK)


class TutorialDetail(generics.RetrieveUpdateAPIView):
    if REMOTE_API:
        authentication_classes = [JWTAuthentication]
    queryset = Tutorial.objects.all()
    serializer_class = TutorialSerializer

    def get(self, request, pk):
        try:
            tutorial = Tutorial.objects.get(pk=pk)
        except Tutorial.DoesNotExist:
            return Response({"message": "fail, tutorial non trovato"}, status=status.HTTP_404_NOT_FOUND)

        # Verifica se l'utente è associato ai progetti collegati al tutorial
        if request.user.is_superadmin() or request.user.is_admin():  # SuperAdmin o Admin
            serializer = TutorialFullSerializer(tutorial)
            return Response(serializer.data, status=status.HTTP_200_OK)

        accessible_project_ids = _accessible_project_ids_for(request.user)
        if not accessible_project_ids:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

        if tutorial.projects.filter(id__in=accessible_project_ids).exists():
            serializer = TutorialFullSerializer(tutorial)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    def delete(self, request, pk):
        try:
            tutorial = Tutorial.objects.get(pk=pk)
        except Exception:
            tutorial = None
        if request.user.is_at_least_associate():
            if tutorial:
                tutorial.delete()
                return Response({"message": "success"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

class TutorialPutView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = TutorialSerializer

    def get(self, request, pk):
        try:
            tutorial = Tutorial.objects.get(pk=pk)
        except Exception:
            tutorial = None
        if request.user.is_at_least_associate():
            if tutorial:
                serializer = TutorialSerializer(tutorial)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "fail, tutorial non trovato"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


    def put(self, request, pk):
        try:
            tutorial = Tutorial.objects.get(pk=pk)
        except Exception:
            tutorial = None
        if request.user.is_at_least_associate():
            if tutorial:
                serializer = TutorialSerializer(tutorial, data=request.data)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    tutorial = serializer.save()
                    try:
                        # Associa i progetti inviati nel request.data
                        tutorial.projects.set(request.data.get('project', []))  # Setta l'elenco dei progetti
                        tutorial.save()
                    except Exception as e:
                        print(f"Errore durante l'aggiornamento dei progetti: {e}")
                    return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
                return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)
            return Response({"message": "fail"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "permission denied"}, status=status.HTTP_403_FORBIDDEN)


class TutorialView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    serializer_class = TutorialSerializer

    def post(self, request, *args, **kwargs):
        if request.user.is_superadmin():
            serializer = TutorialSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                tutorial = serializer.save()
                try:
                    tutorial.projects.set(request.data['project'])
                    tutorial.save()
                except Exception as e: 
                    print(e)
                return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
            return Response({"data": serializer.data, "message": "fail"}, status=status.HTTP_200_OK)
        return Response({"data": serializer.data, "message": "permission denied"}, status=status.HTTP_200_OK)
    
class NoteListCreateView(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        # Associa l'utente autenticato alla nuova nota
        serializer.save(user=self.request.user)

    def post(self, request, *args, **kwargs):
        # Sovrascrivi la risposta per mantenere lo standard richiesto
        response = self.create(request, *args, **kwargs)
        return Response({"data": response.data, "message": "success"}, status=status.HTTP_201_CREATED)


class NoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        # Filtra le note per l'utente autenticato
        user = self.request.user
        return Note.objects.filter(user=user)

    def get(self, request, *args, **kwargs):
        # Sovrascrivi la risposta per mantenere lo standard richiesto
        response = self.retrieve(request, *args, **kwargs)
        return Response({"data": response.data, "message": "success"}, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        # Sovrascrivi la risposta per mantenere lo standard richiesto
        response = self.update(request, *args, **kwargs)
        return Response({"data": response.data, "message": "success"}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        # Sovrascrivi la risposta per mantenere lo standard richiesto
        response = super().delete(request, *args, **kwargs)
        return Response({"message": "success"}, status=status.HTTP_204_NO_CONTENT)
    
class NoteByTutorialView(generics.GenericAPIView):
    serializer_class = NoteSerializer
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]
        
    def get(self, request, *args, **kwargs):
        # Ottieni l'ID del tutorial dalla URL
        tutorial_id = kwargs.get('tutorial_id')
        
        # Cerca la nota associata a questo tutorial e all'utente autenticato
        note = Note.objects.filter(tutorial_id=tutorial_id, user=request.user).first()
        
        if note:
            # Se la nota esiste, serializza e restituisci la risposta con successo
            serializer = self.get_serializer(note)
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
        else:
            # Se la nota non esiste, restituisci un messaggio informativo
            return Response({"data": None, "message": "No note found for the specified tutorial"}, status=status.HTTP_200_OK)

class AddNoteView(APIView):
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        # Recupera i dati dal corpo della richiesta
        tutorial_id = request.data.get('tutorial_id')
        text = request.data.get('text')

        # Verifica che i dati richiesti siano presenti
        if not tutorial_id or not text:
            return Response({"message": "tutorial_id and text are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica l'esistenza del tutorial
        tutorial = Tutorial.objects.filter(id=tutorial_id).first()
        if not tutorial:
            return Response({"message": "Tutorial not found"}, status=status.HTTP_404_NOT_FOUND)

        # Crea la nuova nota associata al cliente autenticato e al tutorial specificato
        note = Note.objects.create(
            text=text,
            tutorial=tutorial,
            user=request.user
        )

        # Serializza la nota appena creata
        serializer = NoteSerializer(note)

        # Restituisci la risposta con lo status di successo
        return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_201_CREATED)
    

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    if REMOTE_API == True:
            authentication_classes = [JWTAuthentication]

    def list(self, request):
        queryset = self.queryset
        serializer = CategorySerializer(queryset, many=True)
        return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = self.queryset.filter(id=pk).first()
        if queryset:
            serializer = CategorySerializer(queryset)
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
        return Response({"data": None, "message": "fail"}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            category = serializer.save()
            try:
                print('request.data: ', request.data)
                # Assegna il valore di parent
                parent_id = request.data.get('parent')
                if parent_id:
                    category.parent_id = parent_id  # Usa parent_id per assegnare direttamente l'ID
                    category.save()
            except Exception as e:
                print(e)
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_201_CREATED)
        return Response({"data": serializer.errors, "message": "fail"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        instance = Category.objects.filter(id=pk).first()
        if not instance:
            return Response({"data": None, "message": "fail"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
        return Response({"data": serializer.errors, "message": "fail"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        instance = Category.objects.filter(id=pk).first()
        if not instance:
            return Response({"data": None, "message": "fail"}, status=status.HTTP_404_NOT_FOUND)

        instance.delete()
        return Response({"data": None, "message": "success"}, status=status.HTTP_204_NO_CONTENT)
