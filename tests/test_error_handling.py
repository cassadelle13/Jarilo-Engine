import requests

# Тест для проверки обработки ошибок
BASE_URL = "http://localhost:8004"

def test_error_handling():
    print("Тестирование обработки ошибок...")

    # Промпт, который вызывает intentional error
    payload = {"prompt": "test_error"}

    try:
        response = requests.post(f"{BASE_URL}/api/v1/tasks/", json=payload, timeout=10)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.json()}")

        # Проверяем, что вернулся 500
        if response.status_code == 500:
            print("✓ Тест пройден: получен корректный HTTP 500 ответ")
            data = response.json()
            if "detail" in data and "Внутренняя ошибка сервера" in data["detail"]:
                print("✓ Тест пройден: корректный формат JSON ответа")
            else:
                print("✗ Тест не пройден: неправильный формат ответа")
        else:
            print(f"✗ Тест не пройден: ожидался 500, получен {response.status_code}")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_error_handling()