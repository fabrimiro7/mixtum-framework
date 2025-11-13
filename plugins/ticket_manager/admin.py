from django.contrib import admin

from plugins.ticket_manager.models import Task, Ticket, Message

admin.site.register(Ticket)
admin.site.register(Task)
admin.site.register(Message)
