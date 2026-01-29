#!/usr/bin/env python3
"""
Тест потокового выполнения shell команд.
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Добавляем путь к brain/src для импорта
import sys
sys.path.insert(0, 'brain/src')

from tools import tool_registry

async def test_shell_streaming():
    print("Тест потокового выполнения shell команд...")

    # Создаем временную директорию для теста
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"Рабочая директория: {temp_dir}")

        # Тест 1: Создание скрипта, который пишет в stdout и stderr
        print("\nТест 1: Создание Python скрипта с выводом в stdout и stderr")
        script_content = '''import sys
print("Это сообщение в stdout")
print("Это сообщение в stderr", file=sys.stderr)
print("Еще одно сообщение в stdout")
'''
        result = await tool_registry.execute_tool("file_tool", "write", path="test_script.py", content=script_content)
        print(f"Результат создания скрипта: {result}")

        # Тест 2: Выполнение скрипта через shell.execute
        print("\nТест 2: Выполнение скрипта через shell.execute")
        result = await tool_registry.execute_tool("shell_tool", "execute", command="python test_script.py")
        print(f"Результат выполнения: {result}")

        # Проверяем, что оба потока захвачены
        output = result.get('output', '')
        if 'stdout' in output.lower() and 'stderr' in output.lower():
            print("✓ Успех: Оба потока (stdout и stderr) захвачены")
        else:
            print("✗ Ошибка: Не все потоки захвачены")
            print(f"Вывод: {output}")

        # Тест 3: Простая команда с stderr
        print("\nТест 3: Простая команда с stderr")
        result = await tool_registry.execute_tool("shell_tool", "execute", command='echo "stdout" && echo "stderr" >&2')
        print(f"Результат выполнения: {result}")

        output = result.get('output', '')
        if 'stdout' in output.lower() and 'stderr' in output.lower():
            print("✓ Успех: Простая команда корректно вывела в оба потока")
        else:
            print("✗ Ошибка: Простая команда не вывела в оба потока")
            print(f"Вывод: {output}")

        print("\nТест завершен!")

if __name__ == "__main__":
    asyncio.run(test_shell_streaming())