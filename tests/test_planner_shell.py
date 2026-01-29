#!/usr/bin/env python3
"""
Тест планировщика с shell.execute
"""

import asyncio
import sys
sys.path.insert(0, 'brain/src')

from orchestration import TaskPlanner

async def test_planner_shell():
    planner = TaskPlanner()
    prompt = 'Создай файл test.txt и напиши в него "шаг 1". Затем выполни команду "echo hello".'
    try:
        plan = await planner.create_plan(prompt)
        print('План:', plan)
        print('Тип плана:', type(plan))
        if isinstance(plan, list):
            for i, item in enumerate(plan):
                print(f'  Шаг {i+1}: {item}')
    except Exception as e:
        print('Ошибка:', e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_planner_shell())