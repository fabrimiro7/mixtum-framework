from typing import Iterable

from base_modules.workspace.models import WorkspaceUser
from plugins.project_manager.models import Project


def requester_shares_workspace_with_project_client(project_id: int, requester_id: int) -> bool:
    """
    Restituisce True se il requester fa parte di almeno uno dei workspace a cui
    appartiene il cliente del progetto identificato da ``project_id``.
    """
    try:
        project = Project.objects.only('client_id').get(id=project_id)
    except Project.DoesNotExist:
        return False

    client_workspace_ids = WorkspaceUser.objects.filter(
        user_id=project.client_id
    ).values_list('workspace_id', flat=True)

    if not any(client_workspace_ids):
        return False

    return WorkspaceUser.objects.filter(
        user_id=requester_id,
        workspace_id__in=list(client_workspace_ids),
    ).exists()
