#!/usr/bin/env python3
"""
Полный интеграционный тест: file + shell operations
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Добавляем путь к brain/src для импорта
import sys
sys.path.insert(0, 'brain/src')

from orchestration import TaskPlanner, TaskExecutor
from workspace.state_manager import StateManager
from orm.db import DatabaseManager

async def test_full_integration():
    print("Полный интеграционный тест: планирование + выполнение с shell.execute")

    # Инициализация компонентов
    db_manager = DatabaseManager()
    await db_manager.init_db()

    state_manager = StateManager()
    planner = TaskPlanner()
    executor = TaskExecutor()

    # Создаем временную директорию для workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"Рабочая директория: {temp_dir}")

        # Тестовый промпт
        prompt = """Создай файл test.txt и напиши в него 'шаг 1'. Затем допиши в этот же файл 'шаг 2'. После этого выполни команду 'cat test.txt' и покажи результат."""

        print(f"Промпт: {prompt}")

        try:
            # Создаем задачу
            task = await state_manager.create_task(prompt=prompt)
            print(f"Задача создана: {task['id']}")

            # Планируем
            plan = await planner.create_plan(prompt=prompt)
            print(f"План: {plan}")

            # Сохраняем план
            await state_manager.update_task_plan(task_id=task['id'], plan=plan)

            # Выполняем
            result = await executor.process_llm_response(plan, task['id'])
            print(f"Результат выполнения: {result}")

            # Проверяем файл
            if os.path.exists('test.txt'):
                with open('test.txt', 'r') as f:
                    content = f.read()
                print(f"Содержимое файла test.txt: {repr(content)}")

                if 'шаг 1' in content and 'шаг 2' in content:
                    print("✓ Успех: Файл содержит оба шага")
                else:
                    print("✗ Ошибка: Файл не содержит ожидаемое содержимое")
            else:
                print("✗ Ошибка: Файл test.txt не создан")

            # Проверяем результат выполнения
            if result and 'шаг 1' in str(result) and 'шаг 2' in str(result):
                print("✓ Успех: Результат выполнения содержит ожидаемый вывод")
            else:
                print("✗ Ошибка: Результат выполнения не содержит ожидаемый вывод")

        except Exception as e:
            print(f"Ошибка в интеграционном тесте: {e}")
            import traceback
            traceback.print_exc()

    await db_manager.close_db()
    print("Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_full_integration())