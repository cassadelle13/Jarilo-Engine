"""
Интеграционный тест для рабочего пространства.
Тестирует создание изолированной директории и монтирование в Docker.
"""

import asyncio
import os
import shutil
import requests
import time
import uuid

# Конфигурация
BASE_URL = "http://localhost:8004"
WORKSPACES_ROOT = "workspaces"


async def test_workspace_integration():
    """
    Интеграционный тест рабочего пространства.
    """
    print("=" * 60)
    print("ИНТЕГРАЦИОННЫЙ ТЕСТ РАБОЧЕГО ПРОСТРАНСТВА")
    print("=" * 60)

    # Шаг 1: Создание задачи с одним шагом
    print("\n[1] Создание задачи...")
    task_prompt = "Создай файл hello.txt с текстом 'Hello, World!' в рабочей директории"
    response = requests.post(
        f"{BASE_URL}/api/v1/tasks/",
        json={"prompt": task_prompt},
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        print(f"✗ Ошибка создания задачи: {response.status_code}")
        print(f"Ответ: {response.text}")
        return False

    task_data = response.json()
    task_id = task_data["id"]
    print(f"✓ Задача создана с ID: {task_id}")

    # Шаг 2: Ожидание завершения выполнения
    print("\n[2] Ожидание выполнения задачи...")
    max_attempts = 30  # 30 секунд
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        if response.status_code == 200:
            task_status = response.json()
            status = task_status.get("status")
            print(f"  Попытка {attempt + 1}: статус {status}")
            if status == "execution_completed":
                break
        time.sleep(1)
    else:
        print("✗ Задача не завершилась в течение 30 секунд")
        return False

    print("✓ Задача выполнена")

    # Шаг 3: Проверка создания файла в рабочем пространстве
    print("\n[3] Проверка рабочего пространства...")
    workspace_path = os.path.join(WORKSPACES_ROOT, task_id)
    test_file_path = os.path.join(workspace_path, "hello.txt")

    if os.path.exists(test_file_path):
        print(f"✓ Файл найден: {test_file_path}")
        # Проверим содержимое файла
        with open(test_file_path, 'r') as f:
            content = f.read().strip()
        if content == "Hello, World!":
            print(f"✓ Содержимое файла корректно: '{content}'")
        else:
            print(f"✗ Содержимое файла некорректно: '{content}'")
            return False
    else:
        print(f"✗ Файл не найден: {test_file_path}")
        return False

    # Шаг 4: Очистка
    print("\n[4] Очистка рабочего пространства...")
    try:
        shutil.rmtree(workspace_path)
        print(f"✓ Директория удалена: {workspace_path}")
    except Exception as e:
        print(f"✗ Ошибка удаления директории: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # Запуск теста в asyncio
    success = asyncio.run(test_workspace_integration())
    exit(0 if success else 1)