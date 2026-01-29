#!/usr/bin/env python3
"""
Комплексный тест арсенала: web + db инструменты
"""

import asyncio
import sys
sys.path.insert(0, 'brain/src')

from tools import tool_registry

async def test_arsenal():
    print("Тест арсенала: web.get + db.query")

    try:
        # Тест 1: Web GET request
        print("\nТест 1: Web GET request")
        result = await tool_registry.execute_tool("web_tool", "get", url="https://httpbin.org/get")
        print(f"Результат web.get: {result}")

        # Тест 2: DB query (read-only)
        print("\nТест 2: DB query")
        # This will fail without proper DB setup, but tests the tool
        result = await tool_registry.execute_tool("db_tool", "query", query="SELECT 1 as test")
        print(f"Результат db.query: {result}")

        # Тест 3: Web POST
        print("\nТест 3: Web POST request")
        result = await tool_registry.execute_tool("web_tool", "post", url="https://httpbin.org/post", data={"test": "data"})
        print(f"Результат web.post: {result}")

        print("\n✓ Тест арсенала завершен!")

    except Exception as e:
        print(f"Ошибка в тесте арсенала: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_arsenal())