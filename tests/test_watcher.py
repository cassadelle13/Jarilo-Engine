"""
Простой тест Смотрителя для проверки обработки ошибок.
"""

import asyncio
import sys
import os

# Добавление пути
sys.path.insert(0, os.path.abspath("brain/src"))

from utils.watcher import watch

async def test_function_success():
    """Тестовая функция, которая выполняется успешно."""
    return "success"

async def test_function_error():
    """Тестовая функция, которая вызывает ошибку."""
    raise ValueError("Тестовая ошибка")

async def main():
    print("Тест Смотрителя")
    print("=" * 30)

    # Тест успешного выполнения
    print("\n1. Тест успешного выполнения:")
    result, error = await watch(test_function_success)()
    print(f"Результат: {result}")
    print(f"Ошибка: {error}")

    # Тест ошибки
    print("\n2. Тест ошибки:")
    result, error = await watch(test_function_error)()
    print(f"Результат: {result}")
    print(f"Ошибка: {error}")

if __name__ == "__main__":
    asyncio.run(main())