"""
Конфигурация Telegram-бота.
Настройки токена, URL API Django и других параметров.
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токен бота из переменной окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# URL Django API
DJANGO_API_URL = 'http://127.0.0.1:8000/api'

# Endpoints API
API_ENDPOINTS = {
    'bind': f'{DJANGO_API_URL}/telegram/bind/',
    'cards': f'{DJANGO_API_URL}/cards/',
    'today': f'{DJANGO_API_URL}/today/',
    'progress': f'{DJANGO_API_URL}/progress/',
    'tts': f'{DJANGO_API_URL}/tts/',
    'test': f'{DJANGO_API_URL}/test/',
    'test_multiple_choice': f'{DJANGO_API_URL}/test/multiple_choice/',
}

# Настройки бота
BOT_COMMANDS = [
    ('start', 'Начать работу с ботом'),
    ('cards', 'Показать все карточки'),
    ('today', 'Карточки на сегодня'),
    ('progress', 'Мой прогресс'),
    ('say', 'Озвучить слово'),
    ('test', 'Пройти тест (знаю/не знаю)'),
    ('test_mc', 'Тест с множественным выбором'),
    ('help', 'Помощь'),
]

# Сообщения бота
MESSAGES = {
    'welcome': 'Привет! Я бот для изучения слов. Используй /help для списка команд.',
    'not_bound': 'Сначала привяжи свой аккаунт. Перейди на сайт и сгенерируй magic-ссылку.',
    'help': '''<b>Доступные команды:</b>
/start — начать работу, привязать аккаунт через magic-ссылку
/help — эта справка
/cards — показать все карточки (первые 10)
/today — карточки на сегодня для повторения
/progress — мой прогресс и статистика
/say слово — озвучить слово (только из своих карточек)
/test — пройти тест по карточкам на сегодня (знаю/не знаю)
/test_mc — пройти тест с множественным выбором

<b>Привязка аккаунта:</b>
- Используй magic-ссылку или QR-код из профиля на сайте.
- После привязки доступны все команды.
''',
    'no_cards': 'У тебя пока нет карточек. Добавь их на сайте!',
    'no_today': 'Сегодня нет карточек для повторения.',
    'word_not_found': 'Слово не найдено в твоих карточках.',
    'error': 'Произошла ошибка. Попробуй позже.',
} 