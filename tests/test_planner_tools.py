#!/usr/bin/env python3
"""
Тест планировщика с инструментами.
"""

import asyncio
import os
import sys

# Добавляем путь к brain/src для импорта
sys.path.insert(0, 'brain/src')

from orchestration.planner import TaskPlanner

async def test_planner_with_tools():
    print("Тест планировщика с инструментами...")

    planner = TaskPlanner()

    # Тест 1: Задача чтения файла
    print("\nТест 1: Задача чтения файла")
    prompt = "Прочитай содержимое файла test.txt"
    plan = await planner.create_plan(prompt)
    print(f"План: {plan}")

    # Тест 2: Задача создания файла
    print("\nТест 2: Задача создания файла")
    prompt = "Создай файл hello.txt и напиши в него 'Hello from tools'"
    plan = await planner.create_plan(prompt)
    print(f"План: {plan}")

if __name__ == "__main__":
    asyncio.run(test_planner_with_tools())