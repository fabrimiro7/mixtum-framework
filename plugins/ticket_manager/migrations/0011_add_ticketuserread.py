# Generated manually for TicketUserRead (Opzione 4 - messaggi non letti)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ticket_manager', '0010_alter_ticket_ticket_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketUserRead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_read_at', models.DateTimeField(auto_now=True)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_by_users', to='ticket_manager.ticket')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_reads', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'TicketUserRead',
                'verbose_name_plural': 'TicketUserReads',
                'unique_together': {('ticket', 'user')},
            },
        ),
    ]
