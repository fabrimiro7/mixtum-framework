from django.db import models
from base_modules.user_manager.models import User
from plugins.project_manager.models import Project

STATUS_CHOICES = (
    ('active', 'Attivo'),
    ('expired', 'Scaduto'),
)

class Subscription(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ManyToManyField(Project, related_name='Progetti', blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    #token = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')


    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ('start_date',)