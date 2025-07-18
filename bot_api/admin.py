from django.contrib import admin
from .models import BotLog

# Register your models here.

@admin.register(BotLog)
class BotLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'telegram_id', 'user', 'success', 'created_at')
    list_filter = ('event_type', 'success', 'created_at')
    search_fields = ('telegram_id', 'request_text', 'response_text')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
