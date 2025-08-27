from django.contrib import admin

from plugins.academy.models import Tutorial
from plugins.academy.models import Note
from plugins.academy.models import Category


admin.site.register(Tutorial)
admin.site.register(Note)
admin.site.register(Category)
