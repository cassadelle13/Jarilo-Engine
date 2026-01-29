#!/usr/bin/env python3
"""
Интеграционный тест: планировщик -> исполнитель -> инструменты.
"""

import asyncio
import os
import sys
import tempfile

# Добавляем путь к brain/src для импорта
sys.path.insert(0, 'brain/src')

from orchestration.planner import TaskPlanner
from orchestration.executor import TaskExecutor
from tools import tool_registry

async def test_full_integration():
    print("Интеграционный тест: планировщик -> исполнитель -> инструменты")

    # Создаем временную директорию для workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        # Устанавливаем переменную окружения для workspace root ПЕРЕД созданием инструментов
        os.environ['JARILO_WORKSPACE_ROOT'] = temp_dir
        print(f"Тестовая директория: {temp_dir}")

        # Создаем новый инструмент с правильным workspace
        from tools.file_tool import FileTool
        file_tool = FileTool()
        file_tool.workspace_root = temp_dir  # Переопределяем workspace root
        
        # Переопределяем execute_tool для использования нашего инструмента
        original_execute = tool_registry.execute_tool
        async def test_execute_tool(tool_name, action, **kwargs):
            if tool_name == "file_tool":
                result = await file_tool.execute(action, **kwargs)
                return {
                    "tool": tool_name,
                    "action": action,
                    "success": result.error is None,
                    "output": result.output,
                    "error": result.error
                }
            else:
                return await original_execute(tool_name, action, **kwargs)
        
        tool_registry.execute_tool = test_execute_tool

        planner = TaskPlanner()
        executor = TaskExecutor()

        # Тест 1: Создание файла
        print("\nТест 1: Создание файла через полный цикл")
        prompt = "Создай файл test_output.txt и напиши в него 'Hello from integration test'"

        # Планирование
        plan = await planner.create_plan(prompt)
        print(f"План: {plan}")

        # Выполнение
        result = await executor.process_llm_response(plan, "test-task-1")
        print(f"Результат выполнения: {result}")

        # Проверка файла
        test_file = os.path.join(temp_dir, "test_output.txt")
        print(f"Проверяем файл: {test_file}")
        print(f"Содержимое директории: {os.listdir(temp_dir)}")
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                content = f.read()
            print(f"Файл создан успешно. Содержимое: '{content}'")
        else:
            print("Ошибка: файл не был создан")

        # Тест 2: Чтение файла
        print("\nТест 2: Чтение файла через полный цикл")
        prompt = "Прочитай содержимое файла test_output.txt"

        # Планирование
        plan = await planner.create_plan(prompt)
        print(f"План: {plan}")

        # Выполнение
        result = await executor.process_llm_response(plan, "test-task-2")
        print(f"Результат выполнения: {result}")

        print("\nИнтеграционный тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_full_integration())