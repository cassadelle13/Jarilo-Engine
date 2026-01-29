"""
Тест стриминга через LangServe эндпоинты.

Этот скрипт тестирует новую систему стриминга, используя HTTP запросы
к эндпоинтам LangServe.
"""

import requests
import json
import threading
import time

# URL сервера
BASE_URL = "http://localhost:8004"

def test_langserve_streaming():
    """Тестирует стриминг через HTTP запросы к LangServe."""
    print("Тестирование LangServe стриминга...")

    # Тестовый промпт
    prompt = "Создай файл test.txt и напиши в него 'Hello from LangServe'."

    payload = {"input": {"prompt": prompt}}

    print(f"Отправка промпта: {prompt}")

    try:
        # Используем stream эндпоинт
        stream_url = f"{BASE_URL}/api/v1/tasks/runnable/stream"
        print(f"Подключение к {stream_url}...")

        response = requests.post(
            stream_url,
            json=payload,
            stream=True,
            timeout=60
        )

        print(f"Статус ответа: {response.status_code}")

        if response.status_code == 200:
            print("Читаем стрим...")
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        try:
                            event = json.loads(data)
                            print(f"Событие: {event}")
                        except json.JSONDecodeError as e:
                            print(f"Не JSON: {data}")
                    elif line.startswith('event: '):
                        print(f"Тип события: {line[7:]}")
        else:
            print(f"Ошибка: {response.text}")

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_langserve_streaming()