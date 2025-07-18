"""
URL configuration for lingua_track project.
Главный роутер: подключает users, cards, core (index), admin.
"""
from django.contrib import admin
from django.urls import path, include
from core.views import index

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin
    path('users/', include('users.urls')),  # Пользовательские маршруты
    path('cards/', include('cards.urls')),  # Карточки
    path('api/', include('bot_api.urls')),  # API для Telegram-бота
    path('', index, name='index'),  # Главная страница
]
