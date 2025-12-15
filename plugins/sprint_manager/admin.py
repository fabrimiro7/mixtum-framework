from django.contrib import admin
from .models import Phase


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'start_date', 'due_date')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'description')
