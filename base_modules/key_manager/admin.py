from django.contrib import admin
from .models import ConfigSetting

@admin.register(ConfigSetting)
class ConfigSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)
