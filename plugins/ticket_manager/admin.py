from django.contrib import admin

from plugins.ticket_manager.models import Ticket, Message

admin.site.register(Ticket)
admin.site.register(Message)
