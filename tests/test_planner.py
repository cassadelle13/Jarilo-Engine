"""
Тест planner.create_plan напрямую.
"""

import asyncio
import sys
import os

# Добавление пути
sys.path.insert(0, os.path.abspath("brain/src"))

from orchestration.planner import TaskPlanner

async def main():
    print("Тест planner.create_plan")
    print("=" * 30)

    planner = TaskPlanner()
    try:
        result = await planner.create_plan("test prompt")
        print(f"Результат: {result}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())