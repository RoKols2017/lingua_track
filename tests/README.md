# 🧪 Тестирование LinguaTrack

Этот каталог содержит все тесты для проекта LinguaTrack.

## 📁 Структура тестов

```
tests/
├── __init__.py              # Пакет тестов
├── conftest.py              # Общие фикстуры
├── utils.py                 # Утилиты для тестов
├── test_sm2.py             # Тесты алгоритма SM-2
├── test_models.py          # Тесты моделей Django
├── test_speechkit.py       # Тесты Yandex SpeechKit
├── test_api.py             # Тесты API endpoints
├── test_forms.py           # Тесты форм Django
├── test_bot.py             # Тесты Telegram-бота
├── test_integration.py     # Интеграционные тесты
└── README.md               # Документация
```

## 🚀 Запуск тестов

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск всех тестов
```bash
pytest
```

### Запуск с покрытием
```bash
pytest --cov=. --cov-report=html
```

### Запуск конкретных тестов
```bash
# Тесты SM-2 алгоритма
pytest tests/test_sm2.py

# Тесты моделей
pytest tests/test_models.py

# Тесты с маркером
pytest -m sm2
pytest -m models
pytest -m integration
```

### Запуск медленных тестов
```bash
pytest -m slow
```

## 🪟 Windows-специфичные команды

### Использование bat-файла (рекомендуется)
```cmd
# Тесты SM-2 алгоритма
.\run_tests.bat --sm2

# Тесты моделей
.\run_tests.bat --models

# Все тесты с покрытием
.\run_tests.bat --coverage

# Все тесты
.\run_tests.bat --all
```

### Использование PowerShell
```powershell
# Установка переменной окружения и запуск
$env:DJANGO_SETTINGS_MODULE="lingua_track.settings"; pytest tests/test_sm2.py

# Или в одну строку
$env:DJANGO_SETTINGS_MODULE="lingua_track.settings"; python -m pytest tests/test_sm2.py -v
```

### Использование Python скрипта
```cmd
# Тесты SM-2 алгоритма
python run_tests.py --sm2

# Тесты моделей
python run_tests.py --models

# С покрытием
python run_tests.py --coverage
```

## 🏷 Маркеры тестов

- `@pytest.mark.unit` - Модульные тесты
- `@pytest.mark.integration` - Интеграционные тесты
- `@pytest.mark.slow` - Медленные тесты
- `@pytest.mark.api` - API тесты
- `@pytest.mark.models` - Тесты моделей
- `@pytest.mark.sm2` - Тесты SM-2 алгоритма
- `@pytest.mark.speechkit` - Тесты SpeechKit
- `@pytest.mark.bot` - Тесты Telegram-бота

## 🎯 Цели покрытия

- **SM-2 алгоритм:** 100%
- **Модели:** 95%
- **SpeechKit:** 90%
- **API:** 85%
- **Формы:** 80%
- **Telegram-бот:** 75%
- **Общее покрытие:** 80%+

## 📊 Покрытие кода

После запуска тестов с покрытием:
1. Откройте `htmlcov/index.html` в браузере
2. Просмотрите детальный отчет по покрытию
3. Найдите непокрытые участки кода

## 🔧 Фикстуры

### Основные фикстуры
- `user` - Тестовый пользователь
- `user_with_telegram` - Пользователь с Telegram ID
- `card` - Тестовая карточка
- `schedule` - Расписание карточки
- `client` - Django тестовый клиент
- `authenticated_client` - Аутентифицированный клиент

### Специализированные фикстуры
- `multiple_cards` - Несколько карточек
- `due_cards` - Карточки готовые к повторению
- `future_cards` - Карточки для будущего повторения
- `mock_speechkit_settings` - Мок настроек SpeechKit
- `sample_csv_file` - Тестовый CSV файл

## 🧪 Примеры тестов

### Тест SM-2 алгоритма
```python
def test_unsuccessful_answer_resets_schedule(schedule_with_history):
    """Тест сброса расписания при неуспешном ответе."""
    schedule = schedule_with_history
    
    # Неуспешный ответ
    update_schedule(schedule, 2)
    
    # Проверяем сброс
    assert schedule.repetition == 0
    assert schedule.interval == 1
    assert schedule.last_result is False
```

### Тест модели
```python
def test_card_creation(user):
    """Тест создания карточки."""
    card = Card.objects.create(
        user=user,
        word='hello',
        translation='привет'
    )
    
    assert card.word == 'hello'
    assert card.translation == 'привет'
    assert hasattr(card, 'schedule')
```

### Тест API
```python
def test_cards_list_api(authenticated_client, card):
    """Тест API получения списка карточек."""
    response = authenticated_client.get('/api/cards/')
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['word'] == 'hello'
```

## 🐛 Отладка тестов

### Показать больше информации
```bash
pytest -v -s
```

### Остановка на первой ошибке
```bash
pytest -x
```

### Запуск конкретного теста
```bash
pytest tests/test_sm2.py::TestSM2Algorithm::test_unsuccessful_answer_resets_schedule
```

### Показать локальные переменные при ошибке
```bash
pytest --tb=long
```

## 🔄 CI/CD

Тесты автоматически запускаются при:
- Push в main ветку
- Pull Request
- Release

### GitHub Actions
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=. --cov-report=xml
```

## 📝 Добавление новых тестов

1. **Создайте файл теста** в соответствующем модуле
2. **Добавьте маркеры** для категоризации
3. **Используйте фикстуры** из conftest.py
4. **Напишите документацию** для теста
5. **Запустите тесты** и проверьте покрытие

### Пример нового теста
```python
@pytest.mark.models
def test_new_feature(user):
    """Тест новой функциональности."""
    # Arrange
    card = create_test_card(user, word='new', translation='новый')
    
    # Act
    result = card.new_method()
    
    # Assert
    assert result == expected_value
```

## 🎯 Лучшие практики

1. **Используйте описательные имена** для тестов
2. **Следуйте паттерну AAA** (Arrange, Act, Assert)
3. **Тестируйте граничные случаи**
4. **Используйте фикстуры** для переиспользования кода
5. **Мокайте внешние зависимости**
6. **Пишите документацию** для сложных тестов
7. **Поддерживайте высокое покрытие** кода

## 🆘 Устранение проблем

### Проблема: Тесты не запускаются
```bash
# Проверьте установку pytest
pip install pytest pytest-django

# Проверьте настройки Django
python manage.py check
```

### Проблема: Ошибка "Database access not allowed" (Windows)
```cmd
# Используйте bat-файл (рекомендуется)
.\run_tests.bat --sm2

# Или установите переменную окружения в PowerShell
$env:DJANGO_SETTINGS_MODULE="lingua_track.settings"; pytest tests/test_sm2.py

# Или используйте Python скрипт
python run_tests.py --sm2
```

### Проблема: "ImportError while loading conftest" (Windows)
```cmd
# Убедитесь, что переменная окружения установлена
echo %DJANGO_SETTINGS_MODULE%

# Если не установлена, используйте bat-файл
.\run_tests.bat --sm2
```

### Проблема: Низкое покрытие
```bash
# Запустите с детальным отчетом
pytest --cov=. --cov-report=term-missing

# Найдите непокрытые строки
pytest --cov=. --cov-report=html
```

### Проблема: Медленные тесты
```bash
# Запустите только быстрые тесты
pytest -m "not slow"

# Используйте параллельное выполнение
pytest -n auto
``` 