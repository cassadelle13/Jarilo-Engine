#!/usr/bin/env python3
"""
Стресс-тест для демонстрации самокоррекции после ошибки выполнения.

Тестовый сценарий: задача "прочитать содержимое файла imaginary_file.txt"
Это гарантированно вызовет ошибку "File not found".
"""

import requests
import json
import time

def test_self_correction():
    """Тестирование способности к самокоррекции после ошибки."""

    # Задача, которая гарантированно вызовет ошибку
    task_data = {
        "prompt": "Прочитай содержимое файла imaginary_file.txt и выведи его на экран."
    }

    print("=== СТРЕСС-ТЕСТ: Самокоррекция после ошибки ===")
    print(f"Задача: {task_data['prompt']}")
    print("Ожидаемая ошибка: FileNotFoundError для imaginary_file.txt")
    print()

    try:
        # Отправка запроса
        response = requests.post(
            "http://localhost:8004/api/v1/tasks/",
            json=task_data,
            timeout=120  # Увеличенный таймаут для полного цикла
        )

        print(f"Статус ответа: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Результат выполнения:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # Анализ результата
            status = result.get("status")
            plan = result.get("plan", [])
            result_output = result.get("result", [])

            print("\nАнализ:")
            print(f"- Статус: {status}")
            print(f"- План: {plan}")
            print(f"- Результаты: {result_output}")

            if status == "failed":
                print("❌ Граф остановился на ошибке - нет самокоррекции")
            elif status == "completed" and "imaginary_file.txt" in str(result_output):
                print("✅ Самокоррекция сработала - задача выполнена несмотря на ошибку")
            else:
                print("⚠️  Неожиданный результат - требуется анализ логов")

        else:
            print(f"Ошибка HTTP: {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print("❌ Таймаут: система не справилась с задачей")
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    test_self_correction()