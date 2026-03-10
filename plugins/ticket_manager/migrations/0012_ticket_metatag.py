# Migration: add Ticket.metatag JSONField (released, released_at)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_manager', '0011_add_ticketuserread'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='metatag',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
