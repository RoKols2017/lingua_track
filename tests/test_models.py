"""
Тесты для моделей Django.

Проверяет корректность работы моделей Card, Schedule, User и BotLog,
включая создание, валидацию, свойства и связи между моделями.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from cards.models import Card, Schedule
from bot_api.models import BotLog
from datetime import date, timedelta

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.models
class TestUserModel:
    """Тесты модели пользователя."""
    
    def test_user_creation(self):
        """Тест создания пользователя."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
    
    def test_user_with_telegram(self):
        """Тест пользователя с привязанным Telegram ID."""
        user = User.objects.create_user(
            username='telegramuser',
            email='telegram@example.com',
            password='testpass123',
            telegram_id=123456789
        )
        
        assert user.telegram_id == 123456789
        assert user.telegram_link_token is None
    
    def test_telegram_id_uniqueness(self, user_with_telegram):
        """Тест уникальности Telegram ID."""
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='anotheruser',
                email='another@example.com',
                password='testpass123',
                telegram_id=user_with_telegram.telegram_id
            )
    
    def test_username_uniqueness(self):
        """Тест уникальности имени пользователя."""
        User.objects.create_user(
            username='uniqueuser',
            email='unique@example.com',
            password='testpass123'
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='uniqueuser',
                email='different@example.com',
                password='testpass123'
            )


@pytest.mark.django_db
@pytest.mark.models
class TestCardModel:
    """Тесты модели карточки."""
    
    def test_card_creation(self, user):
        """Тест создания карточки."""
        card = Card.objects.create(
            user=user,
            word='hello',
            translation='привет',
            example='Hello, world!',
            comment='Приветствие',
            level='beginner'
        )
        
        assert card.word == 'hello'
        assert card.translation == 'привет'
        assert card.example == 'Hello, world!'
        assert card.comment == 'Приветствие'
        assert card.level == 'beginner'
        assert card.user == user
    
    def test_card_string_representation(self, card):
        """Тест строкового представления карточки."""
        assert str(card) == 'hello — привет'
    
    def test_card_level_choices(self, user):
        """Тест выбора уровня сложности."""
        levels = ['beginner', 'intermediate', 'advanced']
        
        for level in levels:
            card = Card.objects.create(
                user=user,
                word=f'test_{level}',
                translation=f'тест_{level}',
                level=level
            )
            assert card.level == level
    
    def test_card_default_level(self, user):
        """Тест уровня по умолчанию."""
        card = Card.objects.create(
            user=user,
            word='test',
            translation='тест'
        )
        assert card.level == 'beginner'
    
    def test_card_ordering(self, user):
        """Тест сортировки карточек."""
        # Создаем карточки в обратном порядке
        card1 = Card.objects.create(
            user=user,
            word='first',
            translation='первый'
        )
        card2 = Card.objects.create(
            user=user,
            word='second',
            translation='второй'
        )
        
        # Получаем карточки пользователя
        cards = Card.objects.filter(user=user)
        
        # Должны быть отсортированы по дате создания (новые сверху)
        assert list(cards) == [card2, card1]
    
    def test_card_user_relationship(self, user, card):
        """Тест связи карточки с пользователем."""
        assert card.user == user
        assert card in user.cards.all()
    
    def test_card_schedule_relationship(self, card):
        """Тест связи карточки с расписанием."""
        assert hasattr(card, 'schedule')
        assert isinstance(card.schedule, Schedule)
        assert card.schedule.card == card


@pytest.mark.django_db
@pytest.mark.models
class TestScheduleModel:
    """Тесты модели расписания."""
    
    def test_schedule_creation(self, card):
        """Тест создания расписания."""
        schedule = Schedule.objects.get(card=card)
        
        assert schedule.card == card
        assert schedule.next_review == date.today()
        assert schedule.interval == 1
        assert schedule.repetition == 0
        assert schedule.ef == 2.5
        assert schedule.last_result is None
    
    def test_schedule_string_representation(self, schedule):
        """Тест строкового представления расписания."""
        expected = f'Schedule for {schedule.card.word} (next: {schedule.next_review})'
        assert str(schedule) == expected
    
    def test_schedule_defaults(self, card):
        """Тест значений по умолчанию."""
        schedule = Schedule.objects.get(card=card)
        
        assert schedule.interval == 1
        assert schedule.repetition == 0
        assert schedule.ef == 2.5
        assert schedule.last_result is None
    
    def test_schedule_is_due_property(self, schedule):
        """Тест свойства is_due."""
        # Сегодня - готово к повторению
        schedule.next_review = date.today()
        schedule.save()
        assert schedule.is_due is True
        
        # Вчера - готово к повторению
        schedule.next_review = date.today() - timedelta(days=1)
        schedule.save()
        assert schedule.is_due is True
        
        # Завтра - не готово
        schedule.next_review = date.today() + timedelta(days=1)
        schedule.save()
        assert schedule.is_due is False
    
    def test_schedule_days_until_review(self, schedule):
        """Тест свойства days_until_review."""
        # Сегодня
        schedule.next_review = date.today()
        schedule.save()
        assert schedule.days_until_review == 0
        
        # Завтра
        schedule.next_review = date.today() + timedelta(days=1)
        schedule.save()
        assert schedule.days_until_review == 1
        
        # Вчера (просрочено)
        schedule.next_review = date.today() - timedelta(days=2)
        schedule.save()
        assert schedule.days_until_review == -2
    
    def test_schedule_ordering(self, user):
        """Тест сортировки расписаний."""
        # Создаем карточки с разными датами
        card1 = Card.objects.create(user=user, word='first', translation='первый')
        card2 = Card.objects.create(user=user, word='second', translation='второй')
        
        schedule1 = Schedule.objects.get(card=card1)
        schedule2 = Schedule.objects.get(card=card2)
        
        # Изменяем даты
        schedule1.next_review = date.today() + timedelta(days=5)
        schedule1.save()
        schedule2.next_review = date.today() + timedelta(days=3)
        schedule2.save()
        
        # Получаем расписания
        schedules = Schedule.objects.filter(card__user=user)
        
        # Должны быть отсортированы по дате повторения
        assert list(schedules) == [schedule2, schedule1]
    
    def test_schedule_one_to_one_relationship(self, card):
        """Тест связи один-к-одному с карточкой."""
        schedule = Schedule.objects.get(card=card)
        
        # Нельзя создать второе расписание для той же карточки
        with pytest.raises(IntegrityError):
            Schedule.objects.create(card=card)


@pytest.mark.django_db
@pytest.mark.models
class TestCardScheduleIntegration:
    """Интеграционные тесты карточек и расписаний."""
    
    def test_automatic_schedule_creation(self, user):
        """Тест автоматического создания расписания при создании карточки."""
        # Создаем карточку
        card = Card.objects.create(
            user=user,
            word='test',
            translation='тест'
        )
        
        # Проверяем, что расписание создалось автоматически
        assert hasattr(card, 'schedule')
        assert card.schedule.card == card
        assert card.schedule.next_review == date.today()
    
    def test_card_properties_with_schedule(self, card):
        """Тест свойств карточки, связанных с расписанием."""
        # Готова к повторению сегодня
        assert card.is_due_for_review is True
        assert card.review_status == 'due'
        
        # Изменяем дату на будущее
        schedule = card.schedule
        schedule.next_review = date.today() + timedelta(days=5)
        schedule.save()
        
        # Обновляем карточку
        card.refresh_from_db()
        assert card.is_due_for_review is False
        assert card.review_status == 'future'
    
    def test_card_without_schedule(self, user):
        """Тест карточки без расписания (edge case)."""
        # Создаем карточку напрямую, минуя сигнал
        card = Card.objects.create(
            user=user,
            word='test',
            translation='тест'
        )
        
        # Удаляем расписание
        Schedule.objects.filter(card=card).delete()
        
        # Обновляем карточку из БД, чтобы сбросить кэш
        card.refresh_from_db()
        
        # Проверяем свойства
        assert card.is_due_for_review is False
        assert card.review_status == 'no_schedule'


@pytest.mark.django_db
@pytest.mark.models
class TestBotLogModel:
    """Тесты модели логов бота."""
    
    def test_botlog_creation(self, user):
        """Тест создания лога бота."""
        log = BotLog.objects.create(
            user=user,
            telegram_id=123456789,
            event_type='command',
            request_text='/test',
            response_text='Тест выполнен',
            success=True
        )
        
        assert log.user == user
        assert log.telegram_id == 123456789
        assert log.event_type == 'command'
        assert log.request_text == '/test'
        assert log.response_text == 'Тест выполнен'
        assert log.success is True
    
    def test_botlog_event_types(self, user):
        """Тест типов событий."""
        event_types = ['message', 'command', 'callback', 'notify', 'error']
        
        for event_type in event_types:
            log = BotLog.objects.create(
                user=user,
                event_type=event_type,
                request_text='test'
            )
            assert log.event_type == event_type
    
    def test_botlog_ordering(self, user):
        """Тест сортировки логов."""
        # Создаем логи с задержкой
        log1 = BotLog.objects.create(
            user=user,
            event_type='command',
            request_text='first'
        )
        
        log2 = BotLog.objects.create(
            user=user,
            event_type='command',
            request_text='second'
        )
        
        # Получаем логи
        logs = BotLog.objects.filter(user=user)
        
        # Должны быть отсортированы по дате создания (новые сверху)
        assert list(logs) == [log2, log1]
    
    def test_botlog_string_representation(self, user):
        """Тест строкового представления лога."""
        log = BotLog.objects.create(
            user=user,
            event_type='command',
            request_text='/test'
        )
        
        # Проверяем формат: "event_type | telegram_id | created_at"
        expected = f'command | None | {log.created_at:%Y-%m-%d %H:%M:%S}'
        assert str(log) == expected
    
    def test_botlog_without_user(self):
        """Тест лога без привязанного пользователя."""
        log = BotLog.objects.create(
            telegram_id=123456789,
            event_type='message',
            request_text='Hello'
        )
        
        assert log.user is None
        assert log.telegram_id == 123456789
    
    def test_botlog_raw_data(self, user):
        """Тест дополнительных данных в JSON."""
        raw_data = {
            'message_id': 123,
            'chat_id': 456,
            'date': 1234567890
        }
        
        log = BotLog.objects.create(
            user=user,
            event_type='message',
            request_text='test',
            raw_data=raw_data
        )
        
        assert log.raw_data == raw_data
        assert log.raw_data['message_id'] == 123 