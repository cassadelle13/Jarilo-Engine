import requests

# Тест для проверки выполнения кода
BASE_URL = "http://localhost:8004"

def test_code_execution():
    print("Тестирование выполнения кода...")

    # Многошаговый промпт для тестирования LLM
    prompt = """Создай файл test.txt и напиши в него 'шаг 1'. Затем допиши в этот же файл 'шаг 2'."""

    payload = {"prompt": prompt}

    try:
        response = requests.post(f"{BASE_URL}/api/v1/tasks/", json=payload, timeout=60)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.json()}")

        if response.status_code == 200:
            task_id = response.json()["id"]
            print(f"Задача создана: {task_id}")

            # Ждем завершения
            import time
            for i in range(30):
                status_response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}", timeout=5)
                if status_response.status_code == 200:
                    data = status_response.json()
                    if data["status"] == "execution_completed":
                        print("Задача выполнена!")
                        print(f"Результат: {data['result']}")
                        break
                time.sleep(1)
            else:
                print("Задача не завершилась вовремя")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_code_execution()