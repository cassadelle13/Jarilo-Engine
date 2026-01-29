#!/usr/bin/env python3
"""
Тестовый скрипт для проверки потоковой передачи событий выполнения задач.

Этот скрипт:
1. Создает новую задачу через POST /api/v1/tasks/
2. Немедленно подключается к потоку событий GET /api/v1/tasks/{task_id}/stream
3. Выводит все поступающие события в реальном времени
4. Завершается при получении TASK_COMPLETED или TASK_FAILED

Использование:
    python test_streaming.py "Создай файл test.txt с текстом 'Hello World'"

Требования:
    - Запущенный сервер Jarilo Brain
    - OPENAI_API_KEY (опционально, будет использовать fallback)
"""

import asyncio
import json
import sys
import requests
import threading
import time
from typing import Optional


class EventStreamer:
    """Класс для чтения и отображения событий из SSE потока."""

    def __init__(self, task_id: str, base_url: str = "http://localhost:8000"):
        self.task_id = task_id
        self.base_url = base_url
        self.stream_url = f"{base_url}/api/v1/tasks/{task_id}/stream"
        self.events_received = []
        self.is_completed = False

    def stream_events(self):
        """Читает события из SSE потока в отдельном потоке."""
        try:
            print(f"🔄 Подключение к потоку событий: {self.stream_url}")

            with requests.get(self.stream_url, stream=True, timeout=60) as response:
                if response.status_code != 200:
                    print(f"❌ Ошибка подключения к потоку: HTTP {response.status_code}")
                    return

                print("✅ Подключение к потоку установлено, ожидаем события...\n")

                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # Убираем 'data: '
                            try:
                                event = json.loads(data)
                                self.events_received.append(event)
                                self.display_event(event)

                                # Проверяем завершающие события
                                if event['event_type'] in ['TASK_COMPLETED', 'TASK_FAILED', 'TASK_NOT_FOUND']:
                                    self.is_completed = True
                                    break

                            except json.JSONDecodeError as e:
                                print(f"❌ Ошибка парсинга события: {e}")
                                print(f"   Raw data: {data}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети при подключении к потоку: {e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка в стриминге: {e}")

    def display_event(self, event: dict):
        """Отображает событие в читаемом формате."""
        event_type = event.get('event_type', 'UNKNOWN')
        timestamp = event.get('timestamp', 'unknown')[:19]  # Только время без микросекунд
        data = event.get('data', {})

        # Цвета для разных типов событий
        colors = {
            'PLAN_GENERATED': '🧠',
            'EXECUTION_STARTED': '▶️',
            'STEP_STARTED': '📍',
            'TOOL_CALLED': '🔧',
            'STEP_COMPLETED': '✅',
            'STEP_FAILED': '❌',
            'AGENT_EXECUTION_STARTED': '🤖',
            'AGENT_EXECUTION_COMPLETED': '🎯',
            'TASK_COMPLETED': '🏁',
            'TASK_FAILED': '💥',
            'HEARTBEAT': '💓',
            'STREAM_ERROR': '🚨',
            'TASK_NOT_FOUND': '🔍'
        }

        icon = colors.get(event_type, '❓')

        print(f"{icon} [{timestamp}] {event_type}")
        if data:
            # Форматируем данные для читаемости
            if event_type == 'PLAN_GENERATED':
                plan = data.get('plan', [])
                print(f"   📋 План с {len(plan)} шагами:")
                for i, step in enumerate(plan, 1):
                    if isinstance(step, dict) and 'tool_name' in step:
                        print(f"      {i}. {step['tool_name']}({step.get('arguments', {})})")

            elif event_type in ['TOOL_CALLED', 'STEP_COMPLETED']:
                if 'tool_name' in data:
                    print(f"   🔧 Инструмент: {data['tool_name']}")
                if 'result' in data:
                    result = str(data['result'])[:100]
                    print(f"   📄 Результат: {result}{'...' if len(str(data['result'])) > 100 else ''}")

            elif event_type == 'TASK_FAILED':
                print(f"   💥 Ошибка: {data.get('error', 'Неизвестная ошибка')}")

            else:
                # Общие данные
                for key, value in data.items():
                    if key != 'task_id':  # Пропускаем task_id для краткости
                        print(f"   {key}: {value}")

        print()  # Пустая строка для разделения событий


async def create_task(prompt: str, base_url: str = "http://localhost:8000") -> Optional[str]:
    """Создает новую задачу и возвращает её ID."""
    url = f"{base_url}/api/v1/tasks/"
    payload = {"prompt": prompt}

    try:
        print(f"📝 Создание задачи: {prompt}")
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get('id')
            print(f"✅ Задача создана с ID: {task_id}")
            return task_id
        else:
            print(f"❌ Ошибка создания задачи: HTTP {response.status_code}")
            print(f"   Ответ: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети при создании задачи: {e}")
        return None


async def main():
    """Основная функция теста."""
    if len(sys.argv) < 2:
        print("Использование: python test_streaming.py \"<описание задачи>\"")
        print("Пример: python test_streaming.py \"Создай файл test.txt с текстом 'Hello World'\"")
        sys.exit(1)

    prompt = sys.argv[1]
    base_url = "http://localhost:8000"  # Можно параметризовать

    print("🎬 Начинаем тест потоковой передачи событий Jarilo")
    print("=" * 60)

    # Создаем задачу
    task_id = await create_task(prompt, base_url)
    if not task_id:
        print("❌ Невозможно продолжить тест без ID задачи")
        sys.exit(1)

    print(f"🎯 Отслеживаем выполнение задачи {task_id}")
    print("-" * 60)

    # Создаем стример событий
    streamer = EventStreamer(task_id, base_url)

    # Запускаем стриминг в отдельном потоке
    stream_thread = threading.Thread(target=streamer.stream_events, daemon=True)
    stream_thread.start()

    # Ждем завершения стрима или таймаута
    timeout = 120  # 2 минуты максимум
    start_time = time.time()

    try:
        while not streamer.is_completed and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)

        if streamer.is_completed:
            print("🏁 Стрим завершен успешно")
        else:
            print(f"⏰ Таймаут {timeout} секунд истек")

    except KeyboardInterrupt:
        print("\n🛑 Тест прерван пользователем")

    # Статистика
    print("\n📊 Статистика:")
    print(f"   Всего событий: {len(streamer.events_received)}")

    event_types = {}
    for event in streamer.events_received:
        event_type = event.get('event_type', 'UNKNOWN')
        event_types[event_type] = event_types.get(event_type, 0) + 1

    print("   По типам:")
    for event_type, count in event_types.items():
        print(f"      {event_type}: {count}")

    print("\n🎪 Тест завершен!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())</content>
<parameter name="filePath">c:\Users\proti\OneDrive\Desktop\jarilo-project\jarilo-ecosystem\test_streaming.py