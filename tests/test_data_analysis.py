#!/usr/bin/env python3
"""
Тест анализа данных с использованием нового плагина data_analyst_plugin.
"""

import requests
import time
import json

def test_data_analysis():
    """Тестирование анализа данных."""

    print("Тестирование анализа данных...")

    # Задача для анализа данных
    task_data = {
        "prompt": "Проанализируй данные в sales.csv и построй график ежемесячных продаж. Сохрани результат как sales_report.png.",
        "workspace_id": "test_data"
    }

    try:
        # Отправляем задачу
        response = requests.post(
            "http://localhost:8004/api/v1/tasks/",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            print(f"Ошибка при создании задачи: {response.status_code}")
            print(response.text)
            return

        result = response.json()
        task_id = result["id"]
        print(f"Задача создана: {task_id}")

        # Ждем выполнения
        time.sleep(2)

        # Ждем завершения задачи
        max_attempts = 30  # 30 секунд максимум
        for attempt in range(max_attempts):
            time.sleep(1)

            # Проверяем статус
            status_response = requests.get(f"http://localhost:8004/api/v1/tasks/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["status"] == "completed":
                    print("Задача завершена успешно!")
                    print(f"План: {status_data['plan']}")
                    print(f"Результат: {status_data['result']}")
                    break
                elif status_data["status"] == "failed":
                    print("Задача завершилась с ошибкой!")
                    print(f"План: {status_data['plan']}")
                    print(f"Результат: {status_data['result']}")
                    break
            else:
                print(f"Ошибка при проверке статуса: {status_response.status_code}")

        else:
            print("Задача не завершилась вовремя")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_data_analysis()