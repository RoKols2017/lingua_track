"""
URL-маршруты для приложения cards.
CRUD для карточек пользователя.
"""
from django.urls import path
from .views import CardListView, CardCreateView, CardUpdateView, CardDeleteView
from .views import review_card, review_mode, import_cards, tts_card, export_cards, test_multiple_choice_view

urlpatterns = [
    path('', CardListView.as_view(), name='card_list'),  # Список и фильтрация карточек
    path('add/', CardCreateView.as_view(), name='card_add'),  # Создание карточки
    path('review/', review_card, name='card_review'),  # Режим повторения
    path('review_mode/', review_mode, name='review_mode'),  # Выбор режима повторения
    path('import/', import_cards, name='card_import'),  # Импорт карточек
    path('export/', export_cards, name='card_export'),  # Экспорт карточек в CSV
    path('test/', test_multiple_choice_view, name='card_test'),  # Тестирование (множественный выбор)
    path('<int:pk>/edit/', CardUpdateView.as_view(), name='card_edit'),  # Редактирование карточки
    path('<int:pk>/delete/', CardDeleteView.as_view(), name='card_delete'),  # Удаление карточки
    path('<int:pk>/tts/', tts_card, name='card_tts'),  # Озвучка карточки (TTS)
] 