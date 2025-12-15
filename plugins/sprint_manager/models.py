from django.db import models
from base_modules.user_manager.models import User
from plugins.project_manager.models import Project

# Create your models here.
TASK_STATUS_CHOICES = (
    ('todo', 'To Do'),
    ('in_progress', 'In corso'),
    ('blocked', 'Bloccato'),
    ('done', 'Completato'),
    ('canceled', 'Annullato'),
)

PRIORITY_CHOICES = (
    ('low', 'Bassa'),
    ('medium', 'Media'),
    ('high', 'Alta'),
)


class Phase(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='phases')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='phases', blank=True, null=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Phase'
        verbose_name_plural = 'Phases'
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.project.title} · {self.title}"
