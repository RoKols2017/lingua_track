"""
Модели приложения cards.

Card — карточка для изучения слов.
Schedule — расписание повторений по алгоритму SM-2 для каждой карточки.

Модели реализуют систему интервального повторения с научно обоснованным
алгоритмом SM-2 для эффективного запоминания иностранных слов.
"""

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    User = AbstractUser
else:
    User = get_user_model()


class Card(models.Model):
    """
    Карточка для изучения иностранного слова.
    
    Привязана к пользователю, содержит слово, перевод, пример, комментарий
    и уровень сложности. Каждая карточка автоматически получает расписание
    повторений при создании.
    
    Attributes:
        user: Владелец карточки (ForeignKey к User).
        word: Слово на иностранном языке (максимум 128 символов).
        translation: Перевод слова (максимум 128 символов).
        example: Пример использования (опционально).
        comment: Комментарий или заметка (опционально).
        level: Уровень сложности (beginner/intermediate/advanced).
        created_at: Дата и время создания карточки.
        updated_at: Дата и время последнего обновления.
    
    Note:
        При создании карточки автоматически создается связанный объект Schedule
        через сигнал post_save.
    """
    
    LEVEL_CHOICES = [
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cards',
        verbose_name='Владелец'
    )
    word = models.CharField(
        max_length=128,
        verbose_name='Слово',
        help_text='Слово на иностранном языке'
    )
    translation = models.CharField(
        max_length=128,
        verbose_name='Перевод',
        help_text='Перевод слова на родной язык'
    )
    example = models.TextField(
        blank=True,
        verbose_name='Пример использования',
        help_text='Пример предложения с этим словом'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий',
        help_text='Дополнительные заметки или пояснения'
    )
    level = models.CharField(
        max_length=16,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name='Уровень',
        help_text='Уровень сложности слова'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )

    class Meta:
        """Мета-класс для настройки модели Card."""
        verbose_name = 'Карточка'
        verbose_name_plural = 'Карточки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'level']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        """Строковое представление: слово и перевод."""
        return f'{self.word} — {self.translation}'

    @property
    def is_due_for_review(self) -> bool:
        """
        Проверяет, нужно ли повторять карточку сегодня.
        
        Returns:
            True если карточка готова к повторению, False иначе.
        """
        if not hasattr(self, 'schedule'):
            return False
        return self.schedule.next_review <= date.today()

    @property
    def review_status(self) -> str:
        """
        Возвращает статус готовности к повторению.
        
        Returns:
            'due' - готова к повторению
            'future' - повторение в будущем
            'no_schedule' - нет расписания
        """
        if not hasattr(self, 'schedule'):
            return 'no_schedule'
        if self.is_due_for_review:
            return 'due'
        return 'future'


class Schedule(models.Model):
    """
    Расписание повторений для карточки по алгоритму SM-2.
    
    Хранит параметры интервального повторения: дату следующего повторения,
    интервал в днях, номер повторения, коэффициент эффективности (EF)
    и результат последнего повторения.
    
    Attributes:
        card: Связанная карточка (OneToOneField к Card).
        next_review: Дата следующего повторения.
        interval: Интервал в днях до следующего повторения.
        repetition: Номер текущего повторения (начинается с 0).
        ef: Коэффициент эффективности SM-2 (от 1.3 до 2.5).
        last_result: Результат последнего повторения (True/False/None).
        updated_at: Дата и время последнего обновления.
    
    Note:
        Алгоритм SM-2 автоматически корректирует интервалы на основе
        качества ответов пользователя.
    """
    
    card = models.OneToOneField(
        Card,
        on_delete=models.CASCADE,
        related_name='schedule',
        verbose_name='Карточка'
    )
    next_review = models.DateField(
        verbose_name='Дата следующего повторения'
    )
    interval = models.PositiveIntegerField(
        default=1,
        verbose_name='Интервал (дней)',
        help_text='Количество дней до следующего повторения'
    )
    repetition = models.PositiveIntegerField(
        default=0,
        verbose_name='Номер повторения',
        help_text='Счетчик успешных повторений подряд'
    )
    ef = models.FloatField(
        default=2.5,
        verbose_name='Эффективность (SM-2)',
        help_text='Коэффициент эффективности от 1.3 до 2.5'
    )
    last_result = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Последний результат (успех)',
        help_text='True - знал, False - не знал, None - не тестировался'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )

    class Meta:
        """Мета-класс для настройки модели Schedule."""
        verbose_name = 'Расписание повторения'
        verbose_name_plural = 'Расписания повторений'
        ordering = ['next_review']
        indexes = [
            models.Index(fields=['next_review']),
            models.Index(fields=['card', 'next_review']),
        ]

    def __str__(self) -> str:
        """Строковое представление: краткая информация о расписании."""
        return f'Schedule for {self.card.word} (next: {self.next_review})'

    @property
    def is_due(self) -> bool:
        """
        Проверяет, нужно ли повторять карточку сегодня.
        
        Returns:
            True если карточка готова к повторению, False иначе.
        """
        return self.next_review <= date.today()

    @property
    def days_until_review(self) -> int:
        """
        Возвращает количество дней до следующего повторения.
        
        Returns:
            Количество дней (отрицательное если просрочено).
        """
        return (self.next_review - date.today()).days


@receiver(post_save, sender=Card)
def create_schedule_for_card(
    sender: type[Card],
    instance: Card,
    created: bool,
    **kwargs
) -> None:
    """
    Автоматически создаёт расписание повторения при создании новой карточки.
    
    Args:
        sender: Класс модели Card.
        instance: Созданный экземпляр карточки.
        created: True если карточка была создана, False если обновлена.
        **kwargs: Дополнительные аргументы сигнала.
    
    Note:
        Расписание создается только для новых карточек, чтобы избежать
        дублирования при обновлении существующих карточек.
    """
    if created and not hasattr(instance, 'schedule'):
        Schedule.objects.create(
            card=instance,
            next_review=date.today()
        )
