# base_modules/user_manager/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

class UsersConfig(AppConfig):
    name = 'base_modules.user_manager'
    verbose_name = "Gestione Utenti"

    def ready(self):
        from base_modules.user_manager import signals 
        post_migrate.connect(create_default_groups, sender=self)

def create_default_groups(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from base_modules.user_manager.models import User

    # Lista dei gruppi da creare
    default_groups = ['administrator', 'moderator', 'user']

    for group_name in default_groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"Creato il gruppo: {group_name}")
            # Assegna i permessi in base al gruppo
            content_type = ContentType.objects.get_for_model(User)
            if group_name == 'administrator':
                # Per il gruppo administrator, assegna tutti i permessi sul modello User
                permissions = Permission.objects.filter(content_type=content_type)
                group.permissions.set(permissions)
            elif group_name == 'moderator':
                # Per il gruppo moderator, assegna permessi specifici (ad esempio, visualizzazione e modifica)
                permission_names = ['view_User', 'change_User']
                permissions = Permission.objects.filter(content_type=content_type, codename__in=permission_names)
                group.permissions.set(permissions)
            elif group_name == 'user':
                # Per il gruppo user, si possono lasciare senza permessi aggiuntivi (o assegnarne alcuni minimi)
                group.permissions.clear()
