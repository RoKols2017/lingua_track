#!/usr/bin/env python
"""
Скрипт для запуска тестов LinguaTrack.

Использование:
    python run_tests.py                    # Все тесты
    python run_tests.py --sm2             # Только SM-2
    python run_tests.py --models          # Только модели
    python run_tests.py --coverage        # С покрытием
    python run_tests.py --fast            # Быстрые тесты
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Запускает команду и выводит результат."""
    print(f"\n{'='*50}")
    print(f"🚀 {description}")
    print(f"{'='*50}")
    print(f"Команда: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} завершено успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} завершено с ошибкой: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Запуск тестов LinguaTrack")
    parser.add_argument("--sm2", action="store_true", help="Тесты SM-2 алгоритма")
    parser.add_argument("--models", action="store_true", help="Тесты моделей")
    parser.add_argument("--api", action="store_true", help="Тесты API")
    parser.add_argument("--forms", action="store_true", help="Тесты форм")
    parser.add_argument("--bot", action="store_true", help="Тесты бота")
    parser.add_argument("--integration", action="store_true", help="Интеграционные тесты")
    parser.add_argument("--coverage", action="store_true", help="С покрытием кода")
    parser.add_argument("--fast", action="store_true", help="Только быстрые тесты")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--stop", "-x", action="store_true", help="Остановка на первой ошибке")
    
    args = parser.parse_args()
    
    # Базовые параметры pytest
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Добавляем флаги
    if args.verbose:
        pytest_cmd.append("-v")
    if args.stop:
        pytest_cmd.append("-x")
    if args.coverage:
        pytest_cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])
    
    # Определяем тесты для запуска
    if args.sm2:
        pytest_cmd.append("tests/test_sm2.py")
        description = "Тесты SM-2 алгоритма"
    elif args.models:
        pytest_cmd.append("tests/test_models.py")
        description = "Тесты моделей"
    elif args.api:
        pytest_cmd.append("tests/test_api.py")
        description = "Тесты API"
    elif args.forms:
        pytest_cmd.append("tests/test_forms.py")
        description = "Тесты форм"
    elif args.bot:
        pytest_cmd.append("tests/test_bot.py")
        description = "Тесты Telegram-бота"
    elif args.integration:
        pytest_cmd.append("tests/test_integration.py")
        description = "Интеграционные тесты"
    else:
        pytest_cmd.append("tests/")
        description = "Все тесты"
    
    # Запускаем тесты
    success = run_command(pytest_cmd, description)
    
    if success:
        print(f"\n🎉 {description} пройдены успешно!")
        if args.coverage:
            print("📊 Отчет о покрытии: htmlcov/index.html")
        sys.exit(0)
    else:
        print(f"\n💥 {description} завершены с ошибками!")
        sys.exit(1)


if __name__ == "__main__":
    main() 