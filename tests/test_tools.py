import requests
import os
import tempfile

# Тест для проверки работы инструментов
BASE_URL = "http://localhost:8000"

def test_file_tools():
    print("Тестирование инструментов работы с файлами...")

    # Создаем временный файл для теста
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello, World!")
        test_file_path = f.name

    try:
        # Тест 1: Чтение файла
        prompt = f'Прочитай содержимое файла "{os.path.basename(test_file_path)}"'

        payload = {"prompt": prompt}

        response = requests.post(f"{BASE_URL}/api/v1/tasks/", json=payload, timeout=60)
        print(f"Тест чтения файла - Статус: {response.status_code}")
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
                        print("Задача чтения выполнена!")
                        print(f"Результат: {data['result']}")
                        break
                time.sleep(1)
            else:
                print("Задача чтения не завершилась вовремя")

        # Тест 2: Запись файла
        prompt = 'Создай файл test_output.txt и напиши в него "Test content from tools"'

        payload = {"prompt": prompt}

        response = requests.post(f"{BASE_URL}/api/v1/tasks/", json=payload, timeout=60)
        print(f"\nТест записи файла - Статус: {response.status_code}")
        print(f"Ответ: {response.json()}")

        if response.status_code == 200:
            task_id = response.json()["id"]
            print(f"Задача создана: {task_id}")

            # Ждем завершения
            for i in range(30):
                status_response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}", timeout=5)
                if status_response.status_code == 200:
                    data = status_response.json()
                    if data["status"] == "execution_completed":
                        print("Задача записи выполнена!")
                        print(f"Результат: {data['result']}")
                        break
                time.sleep(1)
            else:
                print("Задача записи не завершилась вовремя")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        # Очистка
        try:
            os.unlink(test_file_path)
        except:
            pass

if __name__ == "__main__":
    test_file_tools()