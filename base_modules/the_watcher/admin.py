from django.contrib import admin
from .models import Logs

@admin.register(Logs)
class LogsAdmin(admin.ModelAdmin):
    list_display = ('exception_type', 'category', 'timestamp', 'message',)
    list_filter = ('category',)
    search_fields = ('exception_type', 'message', 'category',)
    readonly_fields = ('timestamp',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('exception_type', 'category', 'message', 'extra_data')
        return self.readonly_fields
