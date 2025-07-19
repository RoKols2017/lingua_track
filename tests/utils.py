"""
Утилиты для тестов LinguaTrack.

Содержит вспомогательные функции для создания тестовых данных,
мокирования внешних сервисов и других задач тестирования.
"""

import csv
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from django.core.files.uploadedfile import SimpleUploadedFile
from cards.models import Card, Schedule
from users.models import User


def create_test_csv_file(data: List[Dict[str, Any]], filename: str = "test_cards.csv") -> SimpleUploadedFile:
    """
    Создает временный CSV файл для тестирования импорта.
    
    Args:
        data: Список словарей с данными карточек
        filename: Имя файла
    
    Returns:
        SimpleUploadedFile для использования в тестах
    """
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        temp_path = f.name
    
    # Читаем файл и создаем SimpleUploadedFile
    with open(temp_path, 'rb') as f:
        content = f.read()
    
    # Удаляем временный файл
    Path(temp_path).unlink()
    
    return SimpleUploadedFile(filename, content, content_type='text/csv')


def create_test_user(username: str = "testuser", **kwargs) -> User:
    """
    Создает тестового пользователя.
    
    Args:
        username: Имя пользователя
        **kwargs: Дополнительные параметры
    
    Returns:
        Созданный пользователь
    """
    defaults = {
        'email': f'{username}@example.com',
        'password': 'testpass123'
    }
    defaults.update(kwargs)
    
    return User.objects.create_user(username=username, **defaults)


def create_test_card(user: User, word: str = "test", **kwargs) -> Card:
    """
    Создает тестовую карточку.
    
    Args:
        user: Пользователь-владелец
        word: Слово
        **kwargs: Дополнительные параметры
    
    Returns:
        Созданная карточка
    """
    defaults = {
        'translation': 'тест',
        'level': 'beginner'
    }
    defaults.update(kwargs)
    
    return Card.objects.create(user=user, word=word, **defaults)


def create_test_schedule(card: Card, **kwargs) -> Schedule:
    """
    Создает тестовое расписание для карточки.
    
    Args:
        card: Карточка
        **kwargs: Дополнительные параметры
    
    Returns:
        Созданное расписание
    """
    defaults = {
        'next_review': '2024-01-01',
        'interval': 1,
        'repetition': 0,
        'ef': 2.5
    }
    defaults.update(kwargs)
    
    schedule = Schedule.objects.get(card=card)
    for key, value in defaults.items():
        setattr(schedule, key, value)
    schedule.save()
    
    return schedule


def create_multiple_cards(user: User, count: int = 5) -> List[Card]:
    """
    Создает несколько тестовых карточек.
    
    Args:
        user: Пользователь-владелец
        count: Количество карточек
    
    Returns:
        Список созданных карточек
    """
    cards = []
    words = [
        ('hello', 'привет', 'beginner'),
        ('world', 'мир', 'beginner'),
        ('journey', 'путешествие', 'intermediate'),
        ('sophisticated', 'сложный', 'advanced'),
        ('algorithm', 'алгоритм', 'advanced'),
    ]
    
    for i in range(min(count, len(words))):
        word, translation, level = words[i]
        card = create_test_card(
            user=user,
            word=word,
            translation=translation,
            level=level
        )
        cards.append(card)
    
    return cards


def mock_speechkit_response(success: bool = True, audio_data: bytes = b'fake_audio') -> Dict[str, Any]:
    """
    Создает мок-ответ от SpeechKit.
    
    Args:
        success: Успешность запроса
        audio_data: Аудио данные
    
    Returns:
        Мок-ответ
    """
    if success:
        return {
            'status_code': 200,
            'content': audio_data,
            'headers': {'Content-Type': 'audio/ogg'}
        }
    else:
        return {
            'status_code': 401,
            'content': b'Unauthorized',
            'headers': {'Content-Type': 'text/plain'}
        }


def mock_telegram_response(success: bool = True) -> Dict[str, Any]:
    """
    Создает мок-ответ от Telegram API.
    
    Args:
        success: Успешность запроса
    
    Returns:
        Мок-ответ
    """
    if success:
        return {
            'ok': True,
            'result': {
                'message_id': 123,
                'chat': {'id': 456789},
                'text': 'Test message'
            }
        }
    else:
        return {
            'ok': False,
            'error_code': 400,
            'description': 'Bad Request'
        }


def assert_card_data(card: Card, expected_data: Dict[str, Any]):
    """
    Проверяет соответствие данных карточки ожидаемым.
    
    Args:
        card: Карточка для проверки
        expected_data: Ожидаемые данные
    """
    for field, expected_value in expected_data.items():
        actual_value = getattr(card, field)
        assert actual_value == expected_value, f"{field}: expected {expected_value}, got {actual_value}"


def assert_schedule_data(schedule: Schedule, expected_data: Dict[str, Any]):
    """
    Проверяет соответствие данных расписания ожидаемым.
    
    Args:
        schedule: Расписание для проверки
        expected_data: Ожидаемые данные
    """
    for field, expected_value in expected_data.items():
        actual_value = getattr(schedule, field)
        assert actual_value == expected_value, f"{field}: expected {expected_value}, got {actual_value}"


def create_test_audio_file(filename: str = "test.ogg", content: bytes = b'fake_audio_data') -> SimpleUploadedFile:
    """
    Создает тестовый аудио файл.
    
    Args:
        filename: Имя файла
        content: Содержимое файла
    
    Returns:
        SimpleUploadedFile
    """
    return SimpleUploadedFile(filename, content, content_type='audio/ogg') 