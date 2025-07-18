"""
Модель пользователя (кастомная) для приложения users.

Расширяет AbstractUser, добавляет Telegram ID и токен для привязки.
Реализует систему привязки Telegram-аккаунтов через magic-ссылки.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from typing import Optional


class User(AbstractUser):
    """
    Кастомная модель пользователя с поддержкой Telegram ID и токена для привязки.
    
    Расширяет стандартную модель Django User, добавляя поля для интеграции
    с Telegram-ботом. Позволяет пользователям привязывать свои Telegram-аккаунты
    через magic-ссылки и QR-коды.
    
    Attributes:
        telegram_id: Уникальный ID пользователя в Telegram.
        telegram_link_token: Токен для привязки Telegram-аккаунта.
    
    Note:
        telegram_id должен быть уникальным, так как один Telegram-аккаунт
        может быть привязан только к одному пользователю сайта.
    """
    
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        verbose_name='Telegram ID',
        help_text='Уникальный ID пользователя в Telegram'
    )
    telegram_link_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        verbose_name='Токен для привязки Telegram',
        help_text='Временный токен для привязки Telegram-аккаунта'
    )

    class Meta:
        """Мета-класс для настройки модели User."""
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['telegram_link_token']),
        ]

    def __str__(self) -> str:
        """Строковое представление: имя пользователя."""
        return self.username

    @property
    def is_telegram_bound(self) -> bool:
        """
        Проверяет, привязан ли Telegram-аккаунт.
        
        Returns:
            True если telegram_id установлен, False иначе.
        """
        return self.telegram_id is not None

    @property
    def has_active_token(self) -> bool:
        """
        Проверяет, есть ли активный токен для привязки.
        
        Returns:
            True если telegram_link_token установлен, False иначе.
        """
        return bool(self.telegram_link_token)

    def clear_telegram_token(self) -> None:
        """
        Очищает токен привязки Telegram.
        
        Используется после успешной привязки или истечения срока действия
        токена для безопасности.
        """
        self.telegram_link_token = None
        self.save(update_fields=['telegram_link_token'])

    def bind_telegram(self, telegram_id: int) -> None:
        """
        Привязывает Telegram-аккаунт к пользователю.
        
        Args:
            telegram_id: Telegram ID пользователя.
        
        Note:
            Автоматически очищает токен привязки после успешной привязки.
        """
        self.telegram_id = telegram_id
        self.clear_telegram_token()
        self.save(update_fields=['telegram_id'])

    def unbind_telegram(self) -> None:
        """
        Отвязывает Telegram-аккаунт от пользователя.
        
        Очищает telegram_id и токен привязки.
        """
        self.telegram_id = None
        self.clear_telegram_token()
        self.save(update_fields=['telegram_id'])
