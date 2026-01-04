from base_modules.workspace.models import WorkspaceUser


def user_in_workspace(workspace_id: int, user_id: int) -> bool:
    """
    Restituisce True se l'utente con `user_id` è associato al workspace `workspace_id`.
    """
    return WorkspaceUser.objects.filter(
        workspace_id=workspace_id,
        user_id=user_id,
    ).exists()
