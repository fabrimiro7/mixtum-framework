# workspace/views.py
from base_modules.user_manager.models import User
from rest_framework import viewsets, permissions
from .models import Workspace, WorkspaceUser
from .serializers import WorkspaceSerializer, WorkspaceUserSerializer, UserSerializer

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per visualizzare gli utenti (sola lettura).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet per il modello Workspace.
    Fornisce azioni `list`, `create`, `retrieve`, `update`, `partial_update`, `destroy`.
    """
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    # Potresti voler filtrare i workspace in base all'utente loggato
    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_authenticated:
    #         # Mostra solo i workspace a cui l'utente appartiene
    #         return Workspace.objects.filter(workspaceuser__user=user).distinct()
    #     return Workspace.objects.none() # O tutti, o lancia un errore

class WorkspaceUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet per il modello WorkspaceUser.
    Permette di gestire l'associazione tra utenti e workspace.
    """
    queryset = WorkspaceUser.objects.all()
    serializer_class = WorkspaceUserSerializer

    # Potresti voler filtrare in base al workspace o all'utente
    # Esempio: per mostrare solo le membership dell'utente loggato
    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_authenticated:
    #         return WorkspaceUser.objects.filter(user=user)
    #     return WorkspaceUser.objects.none()

    # Potresti voler impostare l'utente automaticamente durante la creazione
    # def perform_create(self, serializer):
    #     # Se vuoi che un utente possa aggiungere solo se stesso a un workspace
    #     # o se un admin può aggiungere chiunque.
    #     # Qui assumiamo che l'user_id sia passato nel payload,
    #     # altrimenti potresti fare: serializer.save(user=self.request.user)
    #     # se il campo 'user' non fosse read_only nel serializer e 'user_id' non ci fosse.
    #     serializer.save()
