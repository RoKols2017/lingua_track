from django.contrib import admin
from .models import Card, Schedule
from users.models import User
from users.admin import CustomUserAdmin

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('word', 'translation', 'user', 'level', 'created_at', 'updated_at')
    search_fields = ('word', 'translation', 'user__username')
    list_filter = ('level', 'user')
    ordering = ('-created_at',)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('card', 'next_review', 'interval', 'repetition', 'ef', 'last_result', 'updated_at')
    search_fields = ('card__word', 'card__translation', 'card__user__username')
    list_filter = ('next_review', 'interval', 'last_result')
    ordering = ('next_review',)

# Регистрируем пользователя, если не был зарегистрирован
try:
    admin.site.register(User, CustomUserAdmin)
except admin.sites.AlreadyRegistered:
    pass
