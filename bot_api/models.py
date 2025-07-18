"""
Модели приложения bot_api.

BotLog — лог запросов и ответов Telegram-бота для мониторинга и отладки.
"""

from django.db import models
from django.contrib.auth import get_user_model
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    User = AbstractUser
else:
    User = get_user_model()


class BotLog(models.Model):
    """
    Лог запросов и ответов Telegram-бота.
    
    Хранит информацию о взаимодействиях пользователей с ботом для
    мониторинга, отладки и анализа использования системы.
    
    Attributes:
        user: Пользователь (если привязан к аккаунту).
        telegram_id: Telegram ID пользователя.
        event_type: Тип события (message/command/callback/notify/error).
        request_text: Текст запроса от пользователя.
        response_text: Текст ответа бота.
        success: Успешность обработки запроса.
        created_at: Дата и время события.
        raw_data: Дополнительные данные в формате JSON.
    
    Note:
        Модель автоматически сортируется по дате создания (новые сверху).
    """
    
    EVENT_TYPES = [
        ('message', 'Сообщение'),
        ('command', 'Команда'),
        ('callback', 'Callback'),
        ('notify', 'Уведомление'),
        ('error', 'Ошибка'),
    ]
    
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Пользователь',
        help_text='Пользователь сайта (если привязан)'
    )
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Telegram ID',
        help_text='ID пользователя в Telegram'
    )
    event_type = models.CharField(
        max_length=16,
        choices=EVENT_TYPES,
        verbose_name='Тип события',
        help_text='Категория события в боте'
    )
    request_text = models.TextField(
        blank=True,
        verbose_name='Текст запроса',
        help_text='Сообщение или команда от пользователя'
    )
    response_text = models.TextField(
        blank=True,
        verbose_name='Текст ответа',
        help_text='Ответ бота пользователю'
    )
    success = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Успех',
        help_text='True - успешно обработано, False - ошибка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата/время'
    )
    raw_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Сырые данные',
        help_text='Дополнительные данные в формате JSON'
    )

    class Meta:
        """Мета-класс для настройки модели BotLog."""
        verbose_name = 'Лог Telegram-бота'
        verbose_name_plural = 'Логи Telegram-бота'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['success']),
        ]

    def __str__(self) -> str:
        """Строковое представление: тип события, ID и время."""
        return (
            f"{self.event_type} | "
            f"{self.telegram_id} | "
            f"{self.created_at:%Y-%m-%d %H:%M:%S}"
        )

    @classmethod
    def log_event(
        cls,
        event_type: str,
        telegram_id: Optional[int] = None,
        user: Optional[User] = None,
        request_text: str = '',
        response_text: str = '',
        success: Optional[bool] = None,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> 'BotLog':
        """
        Создает новую запись в логе.
        
        Args:
            event_type: Тип события из EVENT_TYPES.
            telegram_id: Telegram ID пользователя.
            user: Пользователь сайта (если привязан).
            request_text: Текст запроса от пользователя.
            response_text: Текст ответа бота.
            success: Успешность обработки.
            raw_data: Дополнительные данные в JSON формате.
        
        Returns:
            Созданный объект BotLog.
        
        Raises:
            ValueError: Если event_type не в списке EVENT_TYPES.
        
        Example:
            >>> BotLog.log_event(
            ...     event_type='command',
            ...     telegram_id=123456789,
            ...     request_text='/help',
            ...     response_text='Справка по командам...',
            ...     success=True
            ... )
        """
        if event_type not in dict(cls.EVENT_TYPES):
            raise ValueError(f"Invalid event_type: {event_type}")
        
        return cls.objects.create(
            event_type=event_type,
            telegram_id=telegram_id,
            user=user,
            request_text=request_text,
            response_text=response_text,
            success=success,
            raw_data=raw_data
        )

    @property
    def is_error(self) -> bool:
        """
        Проверяет, является ли событие ошибкой.
        
        Returns:
            True если event_type == 'error' или success == False.
        """
        return self.event_type == 'error' or self.success is False

    @property
    def duration_ms(self) -> Optional[int]:
        """
        Возвращает длительность обработки в миллисекундах.
        
        Returns:
            Длительность в мс или None если нет данных.
        """
        if not self.raw_data or 'duration_ms' not in self.raw_data:
            return None
        return self.raw_data['duration_ms']
