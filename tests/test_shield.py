#!/usr/bin/env python3
"""
Тест щита: shell.execute с sandboxing
"""

import asyncio
import sys
sys.path.insert(0, 'brain/src')

from tools import tool_registry

async def test_shield():
    print("Тест щита: shell.execute с sandboxing")

    try:
        # Тест 1: Создать файл в первом вызове
        print("\nТест 1: Создание файла в sandbox")
        result = await tool_registry.execute_tool("shell_tool", "execute", command="echo 'test content' > /tmp/test_sandbox.txt && cat /tmp/test_sandbox.txt")
        print(f"Результат первого вызова: {result}")

        # Тест 2: Проверить, что файл не существует во втором вызове (изоляция)
        print("\nТест 2: Проверка изоляции - файл не должен существовать")
        result = await tool_registry.execute_tool("shell_tool", "execute", command="ls -la /tmp/test_sandbox.txt 2>/dev/null || echo 'file not found'")
        print(f"Результат второго вызова: {result}")

        # Тест 3: Проверить ограничения (network, filesystem)
        print("\nТест 3: Проверка ограничений")
        result = await tool_registry.execute_tool("shell_tool", "execute", command="curl -s httpbin.org/get 2>/dev/null || echo 'network blocked'")
        print(f"Результат network test: {result}")

        print("\n✓ Тест щита завершен!")

    except Exception as e:
        print(f"Ошибка в тесте щита: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_shield())