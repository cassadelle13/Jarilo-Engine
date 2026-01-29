#!/usr/bin/env python3
"""
Изолированный тест LangGraph для диагностики бесконечного цикла.

Запускает граф напрямую без FastAPI.
"""

import asyncio
import sys
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Добавляем путь к brain/src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain', 'src'))

from orchestration.graph import compiled_graph

async def test_graph():
    """Тестирование графа с задачей чтения imaginary_file.txt"""

    # Начальное состояние
    initial_state = {
        "task_description": "Прочитай содержимое файла imaginary_file.txt и выведи его на экран.",
        "plan": None,
        "critique": None,
        "tool_calls": [],
        "tool_results": [],
        "replan_attempts": 0,
        "error": ""
    }

    print("=== ЗАПУСК ИЗОЛИРОВАННОГО ТЕСТА ГРАФА ===")
    print(f"Начальное состояние: {initial_state}")
    print()

    try:
        # Запуск графа
        final_state = await compiled_graph.ainvoke(initial_state)

        print("=== ГРАФ ЗАВЕРШЕН ===")
        print(f"Финальное состояние: {final_state}")

    except Exception as e:
        print(f"ОШИБКА В ГРАФЕ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_graph())