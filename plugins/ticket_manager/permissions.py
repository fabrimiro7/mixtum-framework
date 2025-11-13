# permissions.py (nuovo modulo, oppure in views.py se preferisci)
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.db.models import Q
from base_modules.workspace.models import WorkspaceUser

def get_user_workspace_ids(user):
    return list(
        WorkspaceUser.objects.filter(user=user).values_list("workspace_id", flat=True)
    )

def is_superadmin(user):
    return hasattr(user, "is_superadmin") and callable(user.is_superadmin) and user.is_superadmin()

def is_associate(user):
    return hasattr(user, "is_associate") and callable(user.is_associate) and user.is_associate()

def can_access_ticket(user, ticket):
    if is_superadmin(user):
        return True
    ws_ids = get_user_workspace_ids(user)
    in_same_ws = ticket.ticket_workspace_id in ws_ids if ticket.ticket_workspace_id else False
    is_client = (ticket.client_id == user.id)
    is_assignee = ticket.assignees.filter(id=user.id).exists()
    if is_associate(user):
        return in_same_ws or is_assignee or is_client
    return in_same_ws or is_client

# Se vuoi distinguere lettura/scrittura in futuro, ora sono uguali
def can_edit_ticket(user, ticket):
    return can_access_ticket(user, ticket)

class IsWorkspaceMemberOrClientOrAssigneeOrAdmin(BasePermission):
    """
    Permette accesso se:
    - superadmin
    - (associate o utente) e:
        - ticket.ticket_workspace è uno dei workspace dell'utente
        - oppure è client
        - oppure è assignee
    """

    def has_object_permission(self, request, view, obj):
        # obj è un Ticket o un Message: gestisci entrambi
        ticket = obj if hasattr(obj, "ticket_workspace_id") else getattr(obj, "ticket", None)
        if ticket is None:
            return False
        if request.method in SAFE_METHODS:
            return can_access_ticket(request.user, ticket)
        return can_edit_ticket(request.user, ticket)
