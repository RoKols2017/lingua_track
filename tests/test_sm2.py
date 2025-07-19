"""
Тесты для алгоритма SM-2 интервального повторения.

Проверяет корректность работы алгоритма SuperMemo 2 для планирования
повторений карточек на основе качества ответов пользователя.
"""

import pytest
from datetime import date, timedelta
from cards.sm2 import update_schedule
from cards.models import Schedule


@pytest.mark.django_db
@pytest.mark.sm2
class TestSM2Algorithm:
    """Тесты алгоритма SM-2."""
    
    def test_unsuccessful_answer_resets_schedule(self, schedule_with_history):
        """Тест сброса расписания при неуспешном ответе (quality < 3)."""
        schedule = schedule_with_history
        
        # Исходное состояние
        original_repetition = schedule.repetition
        original_interval = schedule.interval
        original_ef = schedule.ef
        
        # Неуспешный ответ
        update_schedule(schedule, 2)
        
        # Проверяем сброс
        assert schedule.repetition == 0
        assert schedule.interval == 1
        assert schedule.last_result is False
        assert schedule.next_review == date.today() + timedelta(days=1)
        
        # EF должен уменьшиться
        assert schedule.ef < original_ef
    
    def test_first_successful_repetition(self, schedule):
        """Тест первого успешного повторения."""
        # Исходное состояние (новое расписание)
        assert schedule.repetition == 0
        assert schedule.interval == 1
        
        # Успешный ответ
        update_schedule(schedule, 4)
        
        # Проверяем результат
        assert schedule.repetition == 1
        assert schedule.interval == 1  # Остается 1 день
        assert schedule.last_result is True
        assert schedule.next_review == date.today() + timedelta(days=1)
    
    def test_second_successful_repetition(self, schedule):
        """Тест второго успешного повторения."""
        # Подготавливаем для второго повторения
        schedule.repetition = 1
        schedule.interval = 1
        schedule.save()
        
        # Успешный ответ
        update_schedule(schedule, 5)
        
        # Проверяем результат
        assert schedule.repetition == 2
        assert schedule.interval == 6  # Должно стать 6 дней
        assert schedule.last_result is True
        assert schedule.next_review == date.today() + timedelta(days=6)
    
    def test_subsequent_successful_repetitions(self, schedule_with_history):
        """Тест последующих успешных повторений."""
        schedule = schedule_with_history
        
        # Исходное состояние
        original_interval = schedule.interval
        original_ef = schedule.ef
        
        # Успешный ответ
        update_schedule(schedule, 4)
        
        # Проверяем результат
        assert schedule.repetition == 4  # Увеличилось с 3
        expected_interval = int(original_interval * original_ef)
        assert schedule.interval == expected_interval
        assert schedule.last_result is True
        assert schedule.next_review == date.today() + timedelta(days=expected_interval)
    
    def test_ef_calculation(self, schedule):
        """Тест расчета коэффициента эффективности (EF)."""
        original_ef = schedule.ef
        
        # Отличный ответ (quality = 5)
        update_schedule(schedule, 5)
        ef_after_excellent = schedule.ef
        assert ef_after_excellent > original_ef
        
        # Хороший ответ (quality = 4) - в SM-2 EF не изменяется при quality=4
        schedule.ef = original_ef  # Сбрасываем
        update_schedule(schedule, 4)
        ef_after_good = schedule.ef
        assert ef_after_good == original_ef  # EF остается тем же при quality=4
        assert ef_after_good < ef_after_excellent
        
        # Плохой ответ (quality = 3)
        schedule.ef = original_ef  # Сбрасываем
        update_schedule(schedule, 3)
        ef_after_poor = schedule.ef
        assert ef_after_poor < original_ef
    
    def test_ef_minimum_boundary(self, schedule):
        """Тест минимальной границы EF (1.3)."""
        # Устанавливаем минимальный EF
        schedule.ef = 1.3
        schedule.save()
        
        # Очень плохой ответ должен оставить EF = 1.3
        update_schedule(schedule, 0)
        assert schedule.ef == 1.3
        
        # Еще один очень плохой ответ
        update_schedule(schedule, 1)
        assert schedule.ef == 1.3
    
    def test_quality_boundaries(self, schedule):
        """Тест граничных значений качества ответа."""
        # Валидные значения
        for quality in [0, 1, 2, 3, 4, 5]:
            update_schedule(schedule, quality)
            assert schedule.last_result == (quality >= 3)
        
        # Невалидные значения должны вызывать исключение
        with pytest.raises(ValueError):
            update_schedule(schedule, -1)
        
        with pytest.raises(ValueError):
            update_schedule(schedule, 6)
    
    def test_schedule_persistence(self, schedule):
        """Тест сохранения изменений в базе данных."""
        original_updated_at = schedule.updated_at
        
        # Обновляем расписание
        update_schedule(schedule, 4)
        
        # Проверяем, что изменения сохранились
        schedule.refresh_from_db()
        assert schedule.repetition == 1
        assert schedule.last_result is True
        assert schedule.updated_at > original_updated_at
    
    def test_multiple_unsuccessful_answers(self, schedule):
        """Тест нескольких неуспешных ответов подряд."""
        # Первый неуспешный ответ
        update_schedule(schedule, 2)
        assert schedule.repetition == 0
        assert schedule.interval == 1
        
        # Второй неуспешный ответ
        update_schedule(schedule, 1)
        assert schedule.repetition == 0
        assert schedule.interval == 1
        
        # Третий неуспешный ответ
        update_schedule(schedule, 0)
        assert schedule.repetition == 0
        assert schedule.interval == 1
    
    def test_mixed_quality_answers(self, schedule):
        """Тест смешанных ответов разного качества."""
        # Успешный ответ
        update_schedule(schedule, 4)
        assert schedule.repetition == 1
        assert schedule.interval == 1
        ef_after_success = schedule.ef
        
        # Неуспешный ответ
        update_schedule(schedule, 2)
        assert schedule.repetition == 0
        assert schedule.interval == 1
        ef_after_failure = schedule.ef
        
        # EF должен уменьшиться после неуспеха
        assert ef_after_failure < ef_after_success
    
    def test_edge_case_quality_3(self, schedule):
        """Тест граничного случая quality = 3 (минимальный успех)."""
        update_schedule(schedule, 3)
        
        # Quality = 3 считается успешным
        assert schedule.last_result is True
        assert schedule.repetition == 1
        assert schedule.interval == 1
    
    def test_edge_case_quality_2(self, schedule):
        """Тест граничного случая quality = 2 (максимальный неуспех)."""
        update_schedule(schedule, 2)
        
        # Quality = 2 считается неуспешным
        assert schedule.last_result is False
        assert schedule.repetition == 0
        assert schedule.interval == 1


@pytest.mark.django_db
@pytest.mark.sm2
class TestSM2Integration:
    """Интеграционные тесты SM-2 с моделями."""
    
    def test_card_creation_creates_schedule(self, user):
        """Тест автоматического создания расписания при создании карточки."""
        from cards.models import Card, Schedule
        
        # Создаем карточку
        card = Card.objects.create(
            user=user,
            word='test',
            translation='тест'
        )
        
        # Проверяем, что расписание создалось автоматически
        assert hasattr(card, 'schedule')
        assert isinstance(card.schedule, Schedule)
        assert card.schedule.next_review == date.today()
        assert card.schedule.repetition == 0
        assert card.schedule.interval == 1
        assert card.schedule.ef == 2.5
    
    def test_card_properties_with_schedule(self, card):
        """Тест свойств карточки, связанных с расписанием."""
        # Карточка готова к повторению сегодня
        assert card.is_due_for_review is True
        assert card.review_status == 'due'
        
        # Изменяем дату на будущее
        schedule = card.schedule
        schedule.next_review = date.today() + timedelta(days=5)
        schedule.save()
        
        # Обновляем карточку из БД
        card.refresh_from_db()
        assert card.is_due_for_review is False
        assert card.review_status == 'future'
    
    def test_schedule_properties(self, schedule):
        """Тест свойств расписания."""
        # Карточка готова к повторению сегодня
        assert schedule.is_due is True
        assert schedule.days_until_review == 0
        
        # Изменяем дату на будущее
        schedule.next_review = date.today() + timedelta(days=3)
        schedule.save()
        
        assert schedule.is_due is False
        assert schedule.days_until_review == 3
        
        # Изменяем дату на прошлое
        schedule.next_review = date.today() - timedelta(days=2)
        schedule.save()
        
        assert schedule.is_due is True
        assert schedule.days_until_review == -2 