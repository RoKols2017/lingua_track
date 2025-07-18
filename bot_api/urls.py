from django.urls import path
from . import views
from .views import telegram_bind, cards_list, cards_today, user_progress, tts, test, test_multiple_choice

urlpatterns = [
    path('telegram/bind/', telegram_bind, name='api_telegram_bind'),
    path('cards/', cards_list, name='api_cards_list'),
    path('today/', cards_today, name='api_cards_today'),
    path('progress/', user_progress, name='api_user_progress'),
    path('tts/', tts, name='api_tts'),
    path('test/', test, name='api_test'),  # опционально
    path('test/multiple_choice/', test_multiple_choice, name='api_test_multiple_choice'),
] 