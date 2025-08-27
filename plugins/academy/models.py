from django.db import models
from base_modules.user_manager.models import User
from  plugins.project_manager.models import Project


TUTORIAL_LEVELS = (
    ('low', 'Bassa'),
    ('medium', 'Media'),
    ('high', 'Alta'),
)

class Category(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subcategories', on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Categories"  

class Tutorial(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    link = models.CharField(max_length=1000)
    insert_date = models.DateTimeField(verbose_name="Data Inserimento", auto_now_add=True)
    projects = models.ManyToManyField(Project, related_name='progetti', blank=True)
    duration = models.CharField(max_length=200, null=True, blank=True)
    level = models.CharField(max_length=200, choices=TUTORIAL_LEVELS, null=True, blank=True, default="low")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutorial_author', null=True, blank=True)
    category = models.ManyToManyField(Category, related_name='tutorial_category', blank=True)

    def __str__(self):
        return self.title + f" (Progetti associati: {self.projects.count()})"


    class Meta:
        verbose_name = 'Tutorial'
        verbose_name_plural = 'Tutorials'
        ordering = ('insert_date',)


class Note(models.Model):
    text = models.TextField(verbose_name="Testo della Nota")
    last_modified = models.DateTimeField(auto_now=True, verbose_name="Ultima Modifica")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notes', verbose_name="Utente")
    tutorial = models.ForeignKey(Tutorial, on_delete=models.CASCADE, related_name='tutorial_notes', verbose_name="Tutorial")

    def __str__(self):
        return f"Nota di {self.user.email} su {self.tutorial.title}"

    class Meta:
        verbose_name = 'Nota'
        verbose_name_plural = 'Note'
        ordering = ('-last_modified',)



