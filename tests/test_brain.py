import requests
import time
import os
import sys


# Конфигурация для тестирования
BASE_URL = "http://localhost:8004"
DB_FILE = "brain/src/jarilo_state.db"


if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование FastAPI-сервиса Jarilo Brain")
    print("=" * 60)
    
    # Шаг 1: Очистка базы данных перед тестом
    print("\n[1] Очистка базы данных перед тестом...")
    # Отключено для тестирования с контейнером
    # if os.path.exists(DB_FILE):
    #     try:
    #         os.remove(DB_FILE)
    #         print(f"    ✓ Удален файл базы данных: {DB_FILE}")
    #     except Exception as e:
    #         print(f"    ✗ Ошибка при удалении файла: {str(e)}")
    # else:
    #     print(f"    ℹ Файл базы данных не найден: {DB_FILE}")
    print("    ℹ Очистка базы отключена для тестирования с контейнером")
    
    # Шаг 2: Проверка доступности сервера (health check)
    print("\n[2] Проверка доступности сервера...")
    for attempt in range(1, 11):
        try:
            response = requests.get(BASE_URL, timeout=5)
            # Сервер ответил (200, 404 или любой другой статус-код)
            if response.status_code in [200, 404]:
                print(f"    ✓ Сервер доступен! (статус {response.status_code})")
                break
        except requests.exceptions.ConnectionError:
            print(f"    ℹ Попытка подключения... ({attempt}/10)")
        except requests.exceptions.Timeout:
            print(f"    ℹ Таймаут при подключении... ({attempt}/10)")
        except Exception as e:
            print(f"    ℹ Ошибка подключения: {str(e)} ({attempt}/10)")
        
        # Пауза между попытками
        time.sleep(1)
    else:
        # Цикл завершился без break (все 10 попыток неудачны)
        print(f"\n    ✗ Сервер не ответил после 10 попыток.")
        print("    Убедитесь, что сервер запущен на http://localhost:8004")
        sys.exit(1)
    
    # Шаг 3: Отправка тестового HTTP-запроса
    print("\n[3] Отправка тестового запроса на создание задачи...")
    
    try:
        # Подготовка URL и данных запроса
        url = f"{BASE_URL}/api/v1/tasks/"
        payload = {
            "prompt": "Создай полнофункциональное веб-приложение для управления задачами с аутентификацией пользователей, REST API, базой данных и современным интерфейсом"
        }
        
        print(f"    URL: POST {url}")
        print(f"    Payload: {payload}")
        
        # Отправка POST-запроса к эндпоинту создания задачи
        response = requests.post(url, json=payload, timeout=30)
        
        # Вывод результатов
        print(f"\n[4] Результаты тестирования:")
        print(f"    Статус-код: {response.status_code}")
        print(f"    Заголовки: {dict(response.headers)}")
        print(f"    Тело ответа:\n{response.json()}")
        
        # Проверка успешности ответа
        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get("id")
            print(f"\n    ✓ Задача создана с ID: {task_id}")
            
            # Ждем выполнения
            print("\n[5] Ожидание выполнения задачи...")
            for i in range(30):  # Ждем до 30 секунд
                status_response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")
                    result = status_data.get("result")
                    print(f"    Статус: {status}")
                    if status == "execution_completed" and result:
                        print(f"    Результат: {result}")
                        print("\n    ✓ Тест пройден успешно!")
                        break
                time.sleep(1)
            else:
                print("\n    ⚠ Задача не завершилась в течение 30 секунд")
        else:
            print(f"\n    ⚠ Сервер вернул статус {response.status_code}")
    
    except requests.exceptions.ConnectionError as e:
        # Обработка ошибки подключения
        print(f"\n    ✗ Ошибка подключения к серверу: {str(e)}")
        print(f"    Убедитесь, что сервер запущен на {BASE_URL}")
    
    except requests.exceptions.Timeout:
        # Обработка таймаута
        print(f"\n    ✗ Таймаут при подключении к серверу")
    
    except Exception as e:
        # Обработка других ошибок
        print(f"\n    ✗ Неожиданная ошибка: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Тестирование завершено")
    print("=" * 60)