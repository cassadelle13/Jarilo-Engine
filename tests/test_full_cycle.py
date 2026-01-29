#!/usr/bin/env python3
"""
Тест полного цикла: planner + executor с shell.execute
"""

import asyncio
import os
import tempfile
import sys
sys.path.insert(0, 'brain/src')

from orchestration import TaskPlanner, TaskExecutor
from workspace.state_manager import StateManager
from orm.db import DatabaseManager

async def test_full_cycle():
    print("Тест полного цикла с shell.execute")

    # Инициализация
    db_manager = DatabaseManager()
    await db_manager.init_db()

    state_manager = StateManager()
    planner = TaskPlanner()
    executor = TaskExecutor()

    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"Рабочая директория: {temp_dir}")

        prompt = 'Создай файл test.txt и напиши в него "шаг 1". Затем выполни команду "echo hello".'

        try:
            # Создаем задачу
            task = await state_manager.create_task(prompt=prompt)
            print(f"Задача: {task['id']}")

            # Планируем
            plan = await planner.create_plan(prompt)
            print(f"План: {plan}")

            # Выполняем
            result = await executor.process_llm_response(plan, task['id'])
            print(f"Результат: {result}")

            # Проверяем файл
            if os.path.exists('test.txt'):
                with open('test.txt', 'r') as f:
                    content = f.read()
                print(f"Файл создан: {content}")

            print("✓ Тест пройден!")

        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()

    await db_manager.close_db()

if __name__ == "__main__":
    asyncio.run(test_full_cycle())