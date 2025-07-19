@echo off
REM Скрипт для запуска тестов LinguaTrack в Windows

set DJANGO_SETTINGS_MODULE=lingua_track.settings

if "%1"=="--sm2" (
    echo Запуск тестов SM-2...
    python -m pytest tests/test_sm2.py -v
) else if "%1"=="--models" (
    echo Запуск тестов моделей...
    python -m pytest tests/test_models.py -v
) else if "%1"=="--coverage" (
    echo Запуск тестов с покрытием...
    python -m pytest --cov=. --cov-report=html --cov-report=term-missing
) else if "%1"=="--all" (
    echo Запуск всех тестов...
    python -m pytest tests/ -v
) else (
    echo Использование: run_tests.bat [--sm2^|--models^|--coverage^|--all]
    echo.
    echo --sm2      - тесты SM-2 алгоритма
    echo --models   - тесты моделей
    echo --coverage - тесты с покрытием кода
    echo --all      - все тесты
) 