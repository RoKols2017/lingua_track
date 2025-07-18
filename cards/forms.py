"""
Формы приложения cards.

CardForm — форма для создания и редактирования карточек.
CardImportForm — форма для импорта карточек из CSV-файла.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import UploadedFile
from typing import TYPE_CHECKING, Optional

from .models import Card

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    User = AbstractUser
else:
    from django.contrib.auth import get_user_model
    User = get_user_model()


class CardForm(forms.ModelForm):
    """
    Форма для создания и редактирования карточек.
    
    Включает все поля модели Card плюс дополнительное поле next_review
    для ручного управления датой следующего повторения.
    
    Attributes:
        next_review: Дата следующего повторения (опционально).
    
    Note:
        Если next_review не указана, используется автоматическое планирование
        по алгоритму SM-2. Если указана - переопределяет автоматическую дату.
    """
    
    next_review = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }
        ),
        label=_('Дата следующего повторения'),
        help_text=_('Оставьте пустым для автоматического планирования')
    )

    class Meta:
        """Мета-класс для настройки формы."""
        model = Card
        fields = ['word', 'translation', 'example', 'comment', 'level']
        widgets = {
            'word': forms.TextInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    'placeholder': _('Введите слово на иностранном языке')
                }
            ),
            'translation': forms.TextInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    'placeholder': _('Введите перевод')
                }
            ),
            'example': forms.Textarea(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    'rows': 3,
                    'placeholder': _('Пример использования (необязательно)')
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    'rows': 2,
                    'placeholder': _('Комментарий или заметка (необязательно)')
                }
            ),
            'level': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        """
        Инициализация формы с установкой даты повторения.
        
        Args:
            *args: Позиционные аргументы для ModelForm.
            **kwargs: Именованные аргументы для ModelForm.
        """
        super().__init__(*args, **kwargs)
        
        # Устанавливаем текущую дату повторения для существующих карточек
        if self.instance and self.instance.pk and hasattr(self.instance, 'schedule'):
            self.fields['next_review'].initial = self.instance.schedule.next_review

    def clean(self) -> dict:
        """
        Валидация формы с проверкой уникальности карточки.
        
        Returns:
            Очищенные данные формы.
        
        Raises:
            ValidationError: Если карточка с таким словом уже существует.
        """
        cleaned_data = super().clean()
        word = cleaned_data.get('word')
        translation = cleaned_data.get('translation')
        
        if word and translation:
            # Проверяем уникальность карточки для пользователя
            existing_cards = Card.objects.filter(
                user=self.instance.user if self.instance.pk else None,
                word__iexact=word.strip(),
                translation__iexact=translation.strip()
            )
            
            if self.instance.pk:
                existing_cards = existing_cards.exclude(pk=self.instance.pk)
            
            if existing_cards.exists():
                raise ValidationError(
                    _('Карточка с таким словом и переводом уже существует.')
                )
        
        return cleaned_data

    def save(self, commit: bool = True) -> Card:
        """
        Сохраняет карточку и обновляет дату повторения.
        
        Args:
            commit: Сохранять ли объект в базу данных.
        
        Returns:
            Сохраненный объект Card.
        
        Note:
            Если указана next_review, обновляет расписание повторения.
        """
        card = super().save(commit=False)
        
        if commit:
            card.save()
            
            # Обновляем дату повторения если указана
            next_review = self.cleaned_data.get('next_review')
            if next_review and hasattr(card, 'schedule'):
                card.schedule.next_review = next_review
                card.schedule.save(update_fields=['next_review'])
        
        return card


class CardImportForm(forms.Form):
    """
    Форма для загрузки CSV-файла с карточками.
    
    Поддерживает импорт карточек из CSV-файла с валидацией формата
    и проверкой дубликатов.
    
    Attributes:
        file: Поле для загрузки CSV-файла.
    
    Note:
        Ожидает CSV-файл в формате: word,translation,example,comment,level
        с кодировкой UTF-8.
    """
    
    file = forms.FileField(
        label=_('CSV-файл'),
        help_text=_('Формат: word,translation,example,comment,level (UTF-8)'),
        widget=forms.FileInput(
            attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'accept': '.csv,text/csv'
            }
        )
    )

    def clean_file(self) -> UploadedFile:
        """
        Валидация загруженного файла.
        
        Returns:
            Валидный файл.
        
        Raises:
            ValidationError: Если файл не соответствует требованиям.
        """
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError(_('Файл не выбран.'))
        
        # Проверяем расширение файла
        if not file.name.lower().endswith('.csv'):
            raise ValidationError(_('Файл должен иметь расширение .csv'))
        
        # Проверяем размер файла (максимум 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError(_('Размер файла не должен превышать 5MB.'))
        
        return file

    def get_csv_data(self) -> list[dict]:
        """
        Извлекает данные из CSV-файла.
        
        Returns:
            Список словарей с данными карточек.
        
        Raises:
            ValidationError: Если формат файла некорректный.
        """
        import csv
        from io import StringIO
        
        file = self.cleaned_data.get('file')
        if not file:
            return []
        
        try:
            # Читаем файл как текст
            content = file.read().decode('utf-8')
            file.seek(0)  # Сбрасываем позицию для повторного чтения
            
            # Парсим CSV
            csv_file = StringIO(content)
            reader = csv.DictReader(csv_file)
            
            # Проверяем обязательные поля
            required_fields = {'word', 'translation'}
            if not required_fields.issubset(set(reader.fieldnames or [])):
                raise ValidationError(
                    _('CSV-файл должен содержать поля: word, translation')
                )
            
            # Извлекаем данные
            cards_data = []
            for row_num, row in enumerate(reader, start=2):  # Начинаем с 2 (заголовок = 1)
                if not row.get('word') or not row.get('translation'):
                    continue  # Пропускаем пустые строки
                
                cards_data.append({
                    'word': row['word'].strip(),
                    'translation': row['translation'].strip(),
                    'example': row.get('example', '').strip(),
                    'comment': row.get('comment', '').strip(),
                    'level': row.get('level', 'beginner').strip(),
                    'row_number': row_num
                })
            
            return cards_data
            
        except UnicodeDecodeError:
            raise ValidationError(_('Файл должен быть в кодировке UTF-8.'))
        except Exception as e:
            raise ValidationError(_(f'Ошибка чтения файла: {str(e)}')) 