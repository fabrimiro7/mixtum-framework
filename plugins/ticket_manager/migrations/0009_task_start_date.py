from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_manager', '0008_ticket_sla_due_at_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]

