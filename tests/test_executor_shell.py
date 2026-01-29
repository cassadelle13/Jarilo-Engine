#!/usr/bin/env python3
"""
Простой тест executor с shell.execute
"""

import asyncio
import os
import tempfile
import sys
sys.path.insert(0, 'brain/src')

from orchestration import TaskExecutor

async def test_executor_shell():
    print("Тест executor с shell.execute")

    executor = TaskExecutor()

    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"Рабочая директория: {temp_dir}")

        # План с shell.execute
        plan = [
            {"tool_name": "file.write", "arguments": {"path": "test.txt", "content": "шаг 1"}},
            {"tool_name": "shell.execute", "arguments": {"command": "echo hello && echo error >&2"}}
        ]

        try:
            result = await executor.process_llm_response(plan, "test-task-id")
            print(f"Результат выполнения: {result}")

            # Проверяем файл
            if os.path.exists('test.txt'):
                with open('test.txt', 'r') as f:
                    content = f.read()
                print(f"Файл test.txt: {repr(content)}")

            # Проверяем результат
            if result and 'hello' in str(result).lower():
                print("✓ Успех: shell.execute выполнен")
            else:
                print("✗ Ошибка: shell.execute не выполнен")

        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_executor_shell())