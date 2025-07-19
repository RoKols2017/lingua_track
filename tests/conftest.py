"""
Общие фикстуры для тестов LinguaTrack.

Содержит фикстуры для создания тестовых данных: пользователей, карточек,
расписаний и других объектов, необходимых для тестирования.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from cards.models import Card, Schedule
from cards.sm2 import update_schedule
from datetime import date, timedelta

User = get_user_model()


@pytest.fixture
def user():
    """Создает тестового пользователя."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def user_with_telegram():
    """Создает пользователя с привязанным Telegram ID."""
    return User.objects.create_user(
        username='telegramuser',
        email='telegram@example.com',
        password='testpass123',
        telegram_id=123456789
    )


@pytest.fixture
def card(user):
    """Создает тестовую карточку."""
    return Card.objects.create(
        user=user,
        word='hello',
        translation='привет',
        example='Hello, world!',
        comment='Приветствие',
        level='beginner'
    )


@pytest.fixture
def card_advanced(user):
    """Создает продвинутую карточку."""
    return Card.objects.create(
        user=user,
        word='sophisticated',
        translation='сложный',
        example='This is a sophisticated algorithm.',
        comment='Сложный алгоритм',
        level='advanced'
    )


@pytest.fixture
def card_intermediate(user):
    """Создает карточку среднего уровня."""
    return Card.objects.create(
        user=user,
        word='journey',
        translation='путешествие',
        example='Life is a journey.',
        comment='Жизненный путь',
        level='intermediate'
    )


@pytest.fixture
def schedule(card):
    """Создает расписание для карточки."""
    return Schedule.objects.get(card=card)


@pytest.fixture
def schedule_with_history(card):
    """Создает расписание с историей повторений."""
    schedule = Schedule.objects.get(card=card)
    # Симулируем историю успешных повторений
    schedule.repetition = 3
    schedule.interval = 15
    schedule.ef = 2.3
    schedule.last_result = True
    schedule.next_review = date.today() - timedelta(days=1)  # Просрочено
    schedule.save()
    return schedule


@pytest.fixture
def schedule_failed(card):
    """Создает расписание с неуспешным последним повторением."""
    schedule = Schedule.objects.get(card=card)
    schedule.repetition = 2
    schedule.interval = 10
    schedule.ef = 2.1
    schedule.last_result = False
    schedule.next_review = date.today() - timedelta(days=2)  # Просрочено
    schedule.save()
    return schedule


@pytest.fixture
def client():
    """Создает тестовый клиент Django."""
    return Client()


@pytest.fixture
def authenticated_client(client, user):
    """Создает аутентифицированный тестовый клиент."""
    client.force_login(user)
    return client


@pytest.fixture
def multiple_cards(user):
    """Создает несколько карточек для тестирования."""
    cards = []
    words = [
        ('hello', 'привет', 'beginner'),
        ('world', 'мир', 'beginner'),
        ('journey', 'путешествие', 'intermediate'),
        ('sophisticated', 'сложный', 'advanced'),
        ('algorithm', 'алгоритм', 'advanced'),
    ]
    
    for word, translation, level in words:
        card = Card.objects.create(
            user=user,
            word=word,
            translation=translation,
            level=level
        )
        cards.append(card)
    
    return cards


@pytest.fixture
def cards_with_schedules(multiple_cards):
    """Создает карточки с разными расписаниями."""
    schedules = []
    for i, card in enumerate(multiple_cards):
        schedule = Schedule.objects.get(card=card)
        # Разные даты повторения
        schedule.next_review = date.today() + timedelta(days=i)
        schedule.repetition = i
        schedule.interval = max(1, i * 2)
        schedule.ef = 2.0 + (i * 0.1)
        schedule.save()
        schedules.append(schedule)
    
    return list(zip(multiple_cards, schedules))


@pytest.fixture
def due_cards(user):
    """Создает карточки, готовые к повторению сегодня."""
    cards = []
    for i in range(3):
        card = Card.objects.create(
            user=user,
            word=f'due_word_{i}',
            translation=f'готовое_слово_{i}',
            level='beginner'
        )
        schedule = Schedule.objects.get(card=card)
        schedule.next_review = date.today()
        schedule.save()
        cards.append(card)
    
    return cards


@pytest.fixture
def future_cards(user):
    """Создает карточки для повторения в будущем."""
    cards = []
    for i in range(3):
        card = Card.objects.create(
            user=user,
            word=f'future_word_{i}',
            translation=f'будущее_слово_{i}',
            level='intermediate'
        )
        schedule = Schedule.objects.get(card=card)
        schedule.next_review = date.today() + timedelta(days=i + 1)
        schedule.save()
        cards.append(card)
    
    return cards


@pytest.fixture
def mock_speechkit_settings(monkeypatch):
    """Мокает настройки SpeechKit для тестов."""
    monkeypatch.setenv('YANDEX_SPEECHKIT_API_KEY', 'test_api_key')
    monkeypatch.setenv('YANDEX_SPEECHKIT_FOLDER_ID', 'test_folder_id')
    monkeypatch.setenv('AUDIO_CACHE_TTL', '604800')


@pytest.fixture
def mock_telegram_settings(monkeypatch):
    """Мокает настройки Telegram для тестов."""
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test_bot_token')


@pytest.fixture
def sample_csv_data():
    """Возвращает тестовые данные CSV для импорта."""
    return [
        {'word': 'apple', 'translation': 'яблоко', 'example': 'An apple a day', 'comment': 'Фрукт', 'level': 'beginner'},
        {'word': 'journey', 'translation': 'путешествие', 'example': 'Life is a journey', 'comment': 'Путь', 'level': 'intermediate'},
        {'word': 'sophisticated', 'translation': 'сложный', 'example': 'Sophisticated algorithm', 'comment': 'Сложный', 'level': 'advanced'},
    ]


@pytest.fixture
def sample_csv_file(tmp_path, sample_csv_data):
    """Создает временный CSV файл с тестовыми данными."""
    import csv
    
    csv_file = tmp_path / "test_cards.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['word', 'translation', 'example', 'comment', 'level'])
        writer.writeheader()
        writer.writerows(sample_csv_data)
    
    return csv_file 