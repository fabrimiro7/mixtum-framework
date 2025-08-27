# workspace/admin.py
from django.contrib import admin
from .models import Workspace, WorkspaceUser

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    """
    Configurazione dell'interfaccia di amministrazione per il modello Workspace.
    """
    list_display = ('workspace_name', 'created_at', 'updated_at')
    search_fields = ('workspace_name', 'workspace_description')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(WorkspaceUser)
class WorkspaceUserAdmin(admin.ModelAdmin):
    """
    Configurazione dell'interfaccia di amministrazione per il modello WorkspaceUser.
    """
    list_display = ('user', 'workspace', 'date_joined')
    search_fields = ('user__username', 'workspace__workspace_name') #
    list_filter = ('workspace', 'date_joined')
    autocomplete_fields = ['user', 'workspace'] 
