# Архитектура Потоковой Передачи Событий Jarilo

## Обзор

**Операция "Живой Поток"** трансформирует архитектуру "Jarilo" из модели "черного ящика" в прозрачную, наблюдаемую систему. Теперь клиенты могут отслеживать выполнение задач в реальном времени через потоковую передачу событий.

## Архитектурные Компоненты

### 1. EventDispatcher (Диспетчер Событий)

**Расположение**: `brain/src/core/event_dispatcher.py`

**Назначение**: Централизованный менеджер очередей событий для каждой активной задачи.

**Ключевые возможности**:
- Создание `asyncio.Queue` для каждой задачи
- Публикация событий от издателей (TaskExecutor, TaskPlanner)
- Подписка на потоки событий для клиентов
- Управление жизненным циклом очередей

**API**:
```python
async def create_task_queue(task_id: str) -> None
async def publish_event(task_id: str, event_type: str, data: dict) -> None
async def subscribe_to_task(task_id: str) -> asyncio.Queue
async def complete_task(task_id: str) -> None
async def fail_task(task_id: str, error: str) -> None
```

### 2. TaskExecutor (Исполнитель Задач)

**Расположение**: `brain/src/orchestration/executor.py`

**Изменения**: Интеграция с EventDispatcher для публикации событий на каждом шаге выполнения.

**Публикуемые события**:
- `EXECUTION_STARTED` - Начало обработки ответа LLM
- `STEP_STARTED` - Начало выполнения шага плана
- `TOOL_CALLED` - Вызов инструмента
- `STEP_COMPLETED` - Шаг выполнен успешно
- `STEP_FAILED` - Ошибка выполнения шага
- `AGENT_EXECUTION_STARTED` - Начало выполнения агента
- `AGENT_EXECUTION_COMPLETED` - Агент завершил выполнение
- `TASK_COMPLETED` - Задача выполнена успешно
- `TASK_FAILED` - Задача провалена

### 3. TaskPlanner (Планировщик Задач)

**Расположение**: `brain/src/orchestration/planner.py`

**Изменения**: Публикация события генерации плана.

**Публикуемые события**:
- `PLAN_GENERATED` - План выполнения сгенерирован

### 4. Streaming API Endpoint

**Эндпоинт**: `GET /api/v1/tasks/{task_id}/stream`

**Расположение**: `brain/src/api/v1/endpoints.py`

**Технология**: Server-Sent Events (SSE) с `StreamingResponse`

**Формат ответа**:
```
data: {"event_type": "STEP_COMPLETED", "timestamp": "2024-01-13T10:30:45.123456Z", "data": {...}}

data: {"event_type": "TASK_COMPLETED", "timestamp": "2024-01-13T10:30:46.789012Z", "data": {"task_id": "..." }}
```

## Формат Событий

### Структура События

```json
{
  "event_type": "string",
  "timestamp": "ISO 8601 string",
  "data": {
    // Зависит от event_type
  }
}
```

### Типы Событий

#### PLAN_GENERATED
Генерация плана выполнения задачи.
```json
{
  "event_type": "PLAN_GENERATED",
  "timestamp": "...",
  "data": {
    "plan": [...],
    "prompt": "string",
    "fallback": false
  }
}
```

#### EXECUTION_STARTED
Начало выполнения задачи.
```json
{
  "event_type": "EXECUTION_STARTED",
  "timestamp": "...",
  "data": {
    "response_type": "list|str"
  }
}
```

#### STEP_STARTED
Начало выполнения шага плана.
```json
{
  "event_type": "STEP_STARTED",
  "timestamp": "...",
  "data": {
    "step": 1,
    "tool_call": {
      "tool_name": "file.write",
      "arguments": {...}
    }
  }
}
```

#### TOOL_CALLED
Вызов инструмента.
```json
{
  "event_type": "TOOL_CALLED",
  "timestamp": "...",
  "data": {
    "tool_name": "file.write",
    "arguments": {...}
  }
}
```

#### STEP_COMPLETED
Шаг выполнен успешно.
```json
{
  "event_type": "STEP_COMPLETED",
  "timestamp": "...",
  "data": {
    "step": 1,
    "result": "..."
  }
}
```

#### STEP_FAILED
Ошибка выполнения шага.
```json
{
  "event_type": "STEP_FAILED",
  "timestamp": "...",
  "data": {
    "step": 1,
    "error": "string"
  }
}
```

#### AGENT_EXECUTION_STARTED
Начало выполнения агента.
```json
{
  "event_type": "AGENT_EXECUTION_STARTED",
  "timestamp": "...",
  "data": {
    "prompt_length": 150
  }
}
```

#### AGENT_EXECUTION_COMPLETED
Агент завершил выполнение.
```json
{
  "event_type": "AGENT_EXECUTION_COMPLETED",
  "timestamp": "...",
  "data": {
    "result_length": 200
  }
}
```

#### TASK_COMPLETED
Задача выполнена успешно.
```json
{
  "event_type": "TASK_COMPLETED",
  "timestamp": "...",
  "data": {
    "task_id": "uuid"
  }
}
```

#### TASK_FAILED
Задача провалена.
```json
{
  "event_type": "TASK_FAILED",
  "timestamp": "...",
  "data": {
    "task_id": "uuid",
    "error": "string"
  }
}
```

## Схема Взаимодействия

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   TaskPlanner   │    │  EventDispatcher │    │   Streaming API │
│                 │    │                  │    │                 │
│ PLAN_GENERATED  │───▶│   publish_event  │    │                 │
│                 │    │                  │    │                 │
└─────────────────┘    │                  │    │                 │
                       │                  │    │                 │
┌─────────────────┐    │  ┌─────────────┐ │    │ ┌─────────────┐ │
│  TaskExecutor   │    │  │  Queue 1    │ │    │ │  Client 1   │ │
│                 │    │  │             │ │    │ │             │ │
│ publish_event   │───▶│  └─────────────┘ │◀───│ │ subscribe    │ │
│                 │    │                  │    │ │             │ │
│ STEP_STARTED    │    │  ┌─────────────┐ │    │ └─────────────┘ │
│ TOOL_CALLED     │    │  │  Queue 2    │ │    │                 │
│ STEP_COMPLETED  │    │  │             │ │    │ ┌─────────────┐ │
│ TASK_COMPLETED  │    │  └─────────────┘ │◀───│ │  Client 2   │ │
│                 │    │                  │    │ │             │ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Тестирование

### Тестовый Скрипт

**Расположение**: `test_streaming.py`

**Использование**:
```bash
python test_streaming.py "Создай файл test.txt с текстом 'Hello World'"
```

**Что делает скрипт**:
1. Создает задачу через POST /api/v1/tasks/
2. Подключается к SSE потоку
3. Отображает события в реальном времени
4. Завершается при TASK_COMPLETED/TASK_FAILED

### Ручное Тестирование

```bash
# Создание задачи
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Создай файл test.txt"}'

# Подключение к потоку (в отдельном терминале)
curl -N http://localhost:8000/api/v1/tasks/{task_id}/stream
```

## Производительность и Масштабируемость

### Оптимизации

1. **AsyncIO Queues**: Неблокирующие очереди для асинхронной коммуникации
2. **Heartbeat**: Периодические сообщения для поддержания соединения
3. **Timeout Handling**: Автоматическое завершение неактивных соединений
4. **Resource Cleanup**: Автоматическая очистка очередей завершенных задач

### Ограничения

- Максимум 30 секунд без событий (heartbeat)
- Очереди существуют только во время выполнения задачи
- SSE не поддерживает бинарные данные

## Безопасность

- CORS headers настроены для веб-клиентов
- Валидация task_id через StateManager
- Ограничение на длительность соединений

## Будущие Улучшения

1. **WebSocket Support**: Для двунаправленной коммуникации
2. **Event Filtering**: Возможность подписки на конкретные типы событий
3. **Event Persistence**: Сохранение истории событий в БД
4. **Metrics Collection**: Сбор статистики по событиям
5. **Client Libraries**: SDK для разных языков программирования

---

**Операция "Живой Поток" завершена успешно!** 🎉

Система Jarilo теперь предоставляет полную прозрачность выполнения задач через потоковую передачу событий в реальном времени.</content>
<parameter name="filePath">c:\Users\proti\OneDrive\Desktop\jarilo-project\jarilo-ecosystem\STREAMING_ARCHITECTURE.md