"""
URL-маршруты для приложения users.
Регистрация, вход, выход, профиль, генерация Telegram-ссылки.
"""
from django.urls import path
from .views import RegisterView, LoginView, logout_view, profile_view, generate_telegram_link, user_progress_view

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # Регистрация
    path('login/', LoginView.as_view(), name='login'),  # Вход
    path('logout/', logout_view, name='logout'),  # Выход
    path('profile/', profile_view, name='profile'),  # Профиль
    path('generate-telegram-link/', generate_telegram_link, name='generate_telegram_link'),  # Magic-ссылка для Telegram
    path('progress/', user_progress_view, name='user_progress'),  # Прогресс пользователя
] 