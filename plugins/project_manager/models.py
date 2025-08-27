from django.db import models
from base_modules.user_manager.models import User

PRIORITY_CHOICES = (
    ('low', 'Bassa'),
    ('medium', 'Media'),
    ('high', 'Alta'),
)

STATUS_CHOICES = (
    ('open', 'Aperto'),
    ('in_progress', 'In corso'),
    ('resolved', 'Risolto'),
    ('closed', 'Chiuso'),
)


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_cliente')
    insert_date = models.DateTimeField(verbose_name="insert_date", auto_now_add=True)
    contributors = models.ManyToManyField(User, related_name='project_contributors', blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ('insert_date',)


