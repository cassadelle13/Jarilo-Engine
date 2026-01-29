#!/usr/bin/env python3
"""
Прямой тест инструментов без Docker.
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Добавляем путь к brain/src для импорта
import sys
sys.path.insert(0, 'brain/src')

from tools import tool_registry

async def test_file_tools_direct():
    print("Прямой тест инструментов работы с файлами...")

    # Создаем временную директорию для теста
    with tempfile.TemporaryDirectory() as temp_dir:
        # Устанавливаем переменную окружения для workspace root
        os.environ['JARILO_WORKSPACE_ROOT'] = temp_dir

        print(f"Тестовая директория: {temp_dir}")

        # Тест 1: Создание файла
        print("\nТест 1: Создание файла")
        result = await tool_registry.execute_tool("file_tool", "write", path="test.txt", content="Hello, World!")
        print(f"Результат: {result}")

        # Тест 2: Чтение файла
        print("\nТест 2: Чтение файла")
        result = await tool_registry.execute_tool("file_tool", "read", path="test.txt")
        print(f"Результат: {result}")

        # Тест 3: Список директории
        print("\nТест 3: Список директории")
        result = await tool_registry.execute_tool("file_tool", "list", path=".")
        print(f"Результат: {result}")

        # Тест 4: Попытка доступа вне workspace (должен быть заблокирован)
        print("\nТест 4: Попытка доступа вне workspace")
        try:
            result = await tool_registry.execute_tool("file_tool", "read", path="../../../etc/passwd")
            print(f"Результат (ожидался отказ): {result}")
        except Exception as e:
            print(f"Ошибка (ожидаемая): {e}")

        # Тест 5: Shell execute
        print("\nТест 5: Shell execute")
        result = await tool_registry.execute_tool("shell_tool", "execute", command="echo 'Hello from shell'")
        print(f"Результат: {result}")

        print("\nВсе тесты завершены!")

if __name__ == "__main__":
    asyncio.run(test_file_tools_direct())