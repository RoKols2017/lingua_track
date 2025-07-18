#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы улучшенной системы озвучки SpeechKit.
Запускать из корня проекта: python test_speechkit.py
"""
import os
import sys
import django
from pathlib import Path

# Настройка Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lingua_track.settings')
django.setup()

from cards.speechkit import (
    synthesize_speech, 
    SpeechKitError, 
    SpeechKitConfigError, 
    SpeechKitAPIError, 
    SpeechKitNetworkError,
    validate_environment,
    clean_audio_cache
)
import logging

# Настройка логирования для тестов
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_configuration():
    """Тестирует валидацию конфигурации."""
    print("=== Тест конфигурации ===")
    try:
        validate_environment()
        print("✅ Конфигурация корректна")
        return True
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def test_synthesis():
    """Тестирует синтез речи для разных языков и fallback."""
    print("\n=== Тест синтеза речи ===")
    test_cases = [
        ("hello world", "en"),
        ("привет мир", "ru"),
        ("bonjour le monde", "fr"),  # не поддерживается, должен быть fallback
        ("test", None),  # автоопределение (en)
        ("тест", None),  # автоопределение (ru)
    ]
    
    for text, lang in test_cases:
        try:
            print(f"Синтезируем: '{text}' (lang={lang})")
            audio_path = synthesize_speech(text, language=lang)
            print(f"✅ Успешно: {audio_path}")
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"   Файл создан: {os.path.getsize(audio_path)} байт")
            else:
                print(f"   ⚠️ Файл не создан или пустой")
        except SpeechKitConfigError as e:
            print(f"❌ Ошибка конфигурации: {e}")
        except SpeechKitAPIError as e:
            print(f"❌ Ошибка API ({e.status_code}): {e.message}")
        except SpeechKitNetworkError as e:
            print(f"❌ Ошибка сети: {e}")
        except SpeechKitError as e:
            print(f"❌ Общая ошибка: {e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")

def test_cache_validation():
    """Тестирует валидацию кэша."""
    print("\n=== Тест валидации кэша ===")
    from cards.speechkit import get_audio_cache_path, is_cache_valid
    
    # Тестируем с несуществующим файлом
    fake_path = get_audio_cache_path("nonexistent")
    print(f"Несуществующий файл: {is_cache_valid(fake_path)}")
    
    # Тестируем с существующим файлом (если есть)
    if os.path.exists("media/audio"):
        audio_files = list(Path("media/audio").glob("*.ogg"))
        if audio_files:
            test_file = audio_files[0]
            print(f"Существующий файл {test_file.name}: {is_cache_valid(test_file)}")
        else:
            print("Нет файлов в кэше для тестирования")

def test_cache_cleanup():
    """Тестирует очистку кэша."""
    print("\n=== Тест очистки кэша ===")
    try:
        print("Очищаем кэш...")
        clean_audio_cache()
        print("✅ Очистка завершена")
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")

def main():
    """Основная функция тестирования."""
    print("🧪 Тестирование улучшенной системы озвучки SpeechKit")
    print("=" * 50)
    
    # Тест 1: Конфигурация
    config_ok = test_configuration()
    
    if config_ok:
        # Тест 2: Синтез речи
        test_synthesis()
        
        # Тест 3: Валидация кэша
        test_cache_validation()
        
        # Тест 4: Очистка кэша
        test_cache_cleanup()
    else:
        print("\n⚠️ Пропускаем тесты синтеза из-за ошибки конфигурации")
        print("Убедитесь, что в .env файле установлены:")
        print("  YANDEX_SPEECHKIT_API_KEY=ваш_ключ")
        print("  YANDEX_SPEECHKIT_FOLDER_ID=ваш_folder_id")
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    main() 