"""
Модуль SM-2 для интервального повторения карточек.

Содержит функцию update_schedule для обновления расписания по алгоритму SM-2.
Алгоритм основан на научных исследованиях эффективности интервального повторения.

References:
    - SuperMemo 2 Algorithm: https://super-memo.com/english/ol/sm2.htm
    - Spaced Repetition: https://en.wikipedia.org/wiki/Spaced_repetition
"""

from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Schedule


def update_schedule(schedule: 'Schedule', quality: int) -> None:
    """
    Обновляет расписание повторения карточки по алгоритму SM-2.
    
    Алгоритм SM-2 адаптирует интервалы повторения на основе качества ответа
    пользователя. При успешных ответах интервал увеличивается экспоненциально,
    при неуспешных - сбрасывается к минимальному значению.
    
    Args:
        schedule: Объект Schedule с текущими параметрами повторения.
        quality: Оценка качества ответа от 0 до 5.
            - 0-2: Не знал (повторение через 1 день)
            - 3-5: Знал (увеличение интервала)
    
    Raises:
        AssertionError: Если quality не в диапазоне [0, 5].
        ValueError: Если schedule не является объектом Schedule.
    
    Note:
        Функция изменяет schedule in-place и автоматически сохраняет изменения.
        
    Example:
        >>> from cards.models import Schedule
        >>> schedule = Schedule.objects.get(id=1)
        >>> update_schedule(schedule, 4)  # Хороший ответ
        >>> print(schedule.interval)  # Увеличенный интервал
        >>> print(schedule.next_review)  # Новая дата повторения
    """
    # Валидация входных параметров
    if not (0 <= quality <= 5):
        raise ValueError(f"Quality must be between 0 and 5, got {quality}")
    
    if not hasattr(schedule, 'interval'):
        raise ValueError("schedule must be a Schedule object")
    
    # Сброс при неуспешном ответе (quality < 3)
    if quality < 3:
        schedule.repetition = 0
        schedule.interval = 1
    else:
        # Успешный ответ - увеличиваем интервал
        if schedule.repetition == 0:
            # Первое успешное повторение
            schedule.interval = 1
        elif schedule.repetition == 1:
            # Второе успешное повторение
            schedule.interval = 6
        else:
            # Последующие повторения: интервал * эффективность
            schedule.interval = int(schedule.interval * schedule.ef)
        
        schedule.repetition += 1
    
    # Обновление коэффициента эффективности (EF)
    # Формула: EF = EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    # Минимальное значение EF = 1.3
    ef_delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    schedule.ef = max(1.3, schedule.ef + ef_delta)
    
    # Расчет следующей даты повторения
    schedule.next_review = date.today() + timedelta(days=schedule.interval)
    
    # Сохранение результата (успех = quality >= 3)
    schedule.last_result = quality >= 3
    
    # Сохранение изменений в базе данных
    schedule.save() 