import requests

# Тест для проверки создания Vite приложения
BASE_URL = "http://localhost:8004"

def test_vite_plugin():
    print("Тестирование плагина Vite...")

    # Промпт для создания Vite приложения
    prompt = """Создай новое React приложение с именем my-vite-app используя Vite."""

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
            for i in range(60):  # Увеличиваем время ожидания для создания приложения
                status_response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}", timeout=5)
                if status_response.status_code == 200:
                    data = status_response.json()
                    if data["status"] == "execution_completed":
                        print("Задача выполнена!")
                        print(f"Результат: {data['result']}")
                        break
                    elif data["status"] == "execution_failed":
                        print("Задача провалилась!")
                        print(f"Ошибка: {data.get('error', 'Неизвестная ошибка')}")
                        break
                time.sleep(2)
            else:
                print("Задача не завершилась вовремя")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_vite_plugin()