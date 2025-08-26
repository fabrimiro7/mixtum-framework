from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import User

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """
    Create default groups and assign permissions on User model.
    Runs after migrations; harmless if re-run.
    """
    default_groups = ["administrator", "moderator", "user"]
    content_type = ContentType.objects.get_for_model(User)

    for group_name in default_groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"Created group: {group_name}")

        if group_name == "administrator":
            permissions = Permission.objects.filter(content_type=content_type)
            group.permissions.set(permissions)
        elif group_name == "moderator":
            # codenames must match your model name 'user'
            permission_names = ["view_user", "change_user"]
            permissions = Permission.objects.filter(content_type=content_type, codename__in=permission_names)
            group.permissions.set(permissions)
        else:
            group.permissions.clear()
