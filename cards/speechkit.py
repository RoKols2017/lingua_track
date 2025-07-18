"""
Модуль для обращения к Yandex SpeechKit (TTS), кеширования аудиофайлов и очистки кеша по TTL.
"""
import os
import requests
import hashlib
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
YANDEX_API_KEY = os.getenv('YANDEX_SPEECHKIT_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_SPEECHKIT_FOLDER_ID')
AUDIO_CACHE_TTL = int(os.getenv('AUDIO_CACHE_TTL', 604800))  # 7 дней по умолчанию
AUDIO_CACHE_DIR = Path('media/audio')
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

SPEECHKIT_URL = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'

# Валидация переменных окружения при импорте модуля
def validate_environment():
    """Проверяет наличие необходимых переменных окружения."""
    missing_vars = []
    
    if not YANDEX_API_KEY:
        missing_vars.append('YANDEX_SPEECHKIT_API_KEY')
    if not YANDEX_FOLDER_ID:
        missing_vars.append('YANDEX_SPEECHKIT_FOLDER_ID')
    
    if missing_vars:
        raise ValueError(
            f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}. "
            f"Добавьте их в файл .env или установите в системе."
        )

# Выполняем валидацию при импорте
try:
    validate_environment()
except ValueError as e:
    logger.error(f"Ошибка конфигурации SpeechKit: {e}")
    # Не прерываем импорт, но логируем ошибку

class SpeechKitError(Exception):
    """Базовый класс для ошибок SpeechKit."""
    pass

class SpeechKitConfigError(SpeechKitError):
    """Ошибка конфигурации SpeechKit."""
    pass

class SpeechKitAPIError(SpeechKitError):
    """Ошибка API SpeechKit."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"SpeechKit API error {status_code}: {message}")

class SpeechKitNetworkError(SpeechKitError):
    """Ошибка сети при обращении к SpeechKit."""
    pass

def get_audio_cache_path(text: str, lang: str = 'en-US', voice: str = 'alena') -> Path:
    """
    Возвращает путь к аудиофайлу для данного текста и параметров.
    """
    key = f'{text}|{lang}|{voice}'
    h = hashlib.sha256(key.encode('utf-8')).hexdigest()
    return AUDIO_CACHE_DIR / f'{h}.ogg'

def is_cache_valid(audio_path: Path) -> bool:
    """
    Проверяет валидность кэшированного файла.
    """
    if not audio_path.exists():
        return False
    
    # Проверяем TTL
    mtime = audio_path.stat().st_mtime
    if time.time() - mtime >= AUDIO_CACHE_TTL:
        return False
    
    # Проверяем размер файла (не должен быть пустым)
    if audio_path.stat().st_size == 0:
        logger.warning(f"Найден пустой кэш-файл: {audio_path}")
        return False
    
    # Проверяем, что файл читается и содержит данные
    try:
        with open(audio_path, 'rb') as f:
            header = f.read(4)
            # Проверяем, что это OGG файл (магические байты OGG)
            if header != b'OggS':
                logger.warning(f"Кэш-файл не является OGG: {audio_path}")
                return False
    except Exception as e:
        logger.warning(f"Ошибка чтения кэш-файла {audio_path}: {e}")
        return False
    
    return True

def make_speechkit_request(text: str, lang: str = 'en-US', voice: str = 'alena', 
                          max_retries: int = 3) -> bytes:
    """
    Выполняет запрос к SpeechKit с retry для 5xx ошибок.
    """
    headers = {
        'Authorization': f'Api-Key {YANDEX_API_KEY}',
    }
    data = {
        'text': text,
        'lang': lang,
        'voice': voice,
        'folderId': YANDEX_FOLDER_ID,
        'format': 'oggopus',
        'sampleRateHertz': '48000',
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Запрос к SpeechKit (попытка {attempt + 1}/{max_retries}): {text}")
            resp = requests.post(SPEECHKIT_URL, headers=headers, data=data, timeout=30)
            
            if resp.status_code == 200:
                return resp.content
            
            # Обработка различных HTTP ошибок
            if resp.status_code == 401:
                raise SpeechKitAPIError(401, "Неверный API ключ. Проверьте YANDEX_SPEECHKIT_API_KEY")
            elif resp.status_code == 403:
                raise SpeechKitAPIError(403, "Доступ запрещен. Проверьте права доступа к SpeechKit")
            elif resp.status_code == 404:
                raise SpeechKitAPIError(404, "Ресурс не найден. Проверьте YANDEX_SPEECHKIT_FOLDER_ID")
            elif resp.status_code == 429:
                raise SpeechKitAPIError(429, "Превышен лимит запросов. Попробуйте позже")
            elif 400 <= resp.status_code < 500:
                raise SpeechKitAPIError(resp.status_code, f"Ошибка клиента: {resp.text}")
            elif 500 <= resp.status_code < 600:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Экспоненциальная задержка
                    logger.warning(f"Ошибка сервера {resp.status_code}, повтор через {wait_time}с")
                    time.sleep(wait_time)
                    continue
                else:
                    raise SpeechKitAPIError(resp.status_code, f"Ошибка сервера после {max_retries} попыток: {resp.text}")
            else:
                raise SpeechKitAPIError(resp.status_code, f"Неожиданный статус: {resp.text}")
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                logger.warning(f"Таймаут запроса (попытка {attempt + 1}), повтор...")
                time.sleep(1)
                continue
            else:
                raise SpeechKitNetworkError("Таймаут запроса к SpeechKit после всех попыток")
                
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Ошибка соединения (попытка {attempt + 1}), повтор...")
                time.sleep(1)
                continue
            else:
                raise SpeechKitNetworkError(f"Ошибка соединения с SpeechKit: {e}")
                
        except requests.exceptions.RequestException as e:
            raise SpeechKitNetworkError(f"Ошибка сети при обращении к SpeechKit: {e}")
    
    # Не должно дойти до сюда
    raise SpeechKitError("Неожиданная ошибка в make_speechkit_request")

# Маппинг голосов по языкам
VOICE_MAPPING = {
    'en': 'jane',    # английский женский голос (можно zahar)
    'ru': 'alena',   # русский женский голос (можно ermil)
}
DEFAULT_VOICE = 'jane'  # fallback голос
SUPPORTED_LANGUAGES = set(VOICE_MAPPING.keys())

VOICE_OPTIONS = {
    'en': ['jane', 'zahar'],
    'ru': ['alena', 'ermil'],
}
VOICE_LANG_CODE = {
    'en': 'en-US',
    'ru': 'ru-RU',
}

def detect_language(text: str) -> str:
    """
    Примитивная эвристика: если есть кириллица — ru, иначе en.
    Можно заменить на полноценную библиотеку langdetect при необходимости.
    """
    import re
    if re.search(r'[а-яА-ЯёЁ]', text):
        return 'ru'
    return 'en'

def synthesize_speech(text: str, language: str = None, voice: str = None) -> str:
    """
    Получает аудиофайл для текста через Yandex SpeechKit с кешированием.
    language: 'en', 'ru' или None (автоопределение)
    voice: если явно указан — использовать, иначе выбрать по языку
    Если voice не подходит к языку — fallback на дефолтный.
    """
    # Проверяем конфигурацию
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        raise SpeechKitConfigError(
            "SpeechKit не настроен. Проверьте переменные окружения: "
            "YANDEX_SPEECHKIT_API_KEY и YANDEX_SPEECHKIT_FOLDER_ID"
        )
    
    # Валидация входных параметров
    if not text or not text.strip():
        raise ValueError("Текст для озвучки не может быть пустым")
    text = text.strip()
    
    # Определяем язык, если не задан
    lang = language or detect_language(text)
    if lang not in SUPPORTED_LANGUAGES:
        lang = 'en'  # fallback
    allowed_voices = VOICE_OPTIONS[lang]
    # Если передан voice, но он не подходит — fallback
    if voice not in allowed_voices:
        selected_voice = VOICE_MAPPING[lang]
    else:
        selected_voice = voice
    
    audio_path = get_audio_cache_path(text, lang, selected_voice)
    
    # Проверка кэша
    if is_cache_valid(audio_path):
        logger.info(f"Используется кэш для: {text} ({lang}, {selected_voice})")
        return str(audio_path)
    
    # Удаляем битый кэш если есть
    if audio_path.exists():
        try:
            audio_path.unlink()
            logger.info(f"Удален битый кэш: {audio_path}")
        except Exception as e:
            logger.warning(f"Не удалось удалить битый кэш {audio_path}: {e}")
    
    # Запрос к SpeechKit
    try:
        audio_data = make_speechkit_request(
            text,
            lang=VOICE_LANG_CODE[lang],
            voice=selected_voice
        )
        # Сохраняем в кэш
        try:
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"Сохранен в кэш: {text} -> {audio_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш {audio_path}: {e}")
            raise SpeechKitError(f"Не удалось сохранить аудио в кэш: {e}")
        return str(audio_path)
    except (SpeechKitAPIError, SpeechKitNetworkError, SpeechKitConfigError):
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при синтезе речи для '{text}': {e}")
        raise SpeechKitError(f"Ошибка синтеза речи: {e}")

def clean_audio_cache():
    """
    Удаляет аудиофайлы старше TTL из кеша.
    """
    now = time.time()
    deleted_count = 0
    
    for file in AUDIO_CACHE_DIR.glob('*.ogg'):
        try:
            if now - file.stat().st_mtime > AUDIO_CACHE_TTL:
                file.unlink()
                deleted_count += 1
        except Exception as e:
            logger.warning(f"Не удалось удалить кэш-файл {file}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Очищено {deleted_count} устаревших кэш-файлов") 