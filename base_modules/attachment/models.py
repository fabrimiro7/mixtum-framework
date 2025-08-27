from django.db import models
from django.core.validators import MinLengthValidator
from base_modules.user_manager.models import User

class Attachment(models.Model):
 
    title = models.CharField(max_length=200, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_attachment')
    creation_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(blank=True, null=True,)
    description = models.CharField(max_length=2000, null=True, blank=True)
    
    def __str__(self):
        return str(self.title)
        
    class Meta:
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'
        ordering = ('id',)

