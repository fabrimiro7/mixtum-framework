from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('per_seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='sitemap_url',
            field=models.TextField(blank=True, null=True),
        ),
    ]
