from pydantic import BaseModel, Field
from typing import Dict, Optional


# Протокол общения между компонентами Jarilo (адаптирован из AutoGen)
class AgentMessage(BaseModel):
    """
    Структура сообщения для общения между brain и микро-агентами.
    
    Адаптирована из архитектуры AutoGen для стандартизации протокола
    обмена данными между компонентами мультиагентной системы Jarilo.
    
    Использование:
        - Brain отправляет задачи микро-агентам через AgentMessage
        - Микро-агенты отвечают результатами в той же структуре
        - Структура обеспечивает единообразное представление данных
    
    Преимущества:
        - Типизированная валидация данных через Pydantic
        - Расширяемость через поле metadata
        - Совместимость с JSON для передачи по сети
        - Стандартизированный протокол для всех агентов
    
    Поля:
        role (str): Роль отправителя сообщения.
                   Примеры: "user_proxy" (brain), "assistant" (микро-агент).
        content (str): Основное содержание сообщения (задача, результат, и т.д.).
        metadata (Optional[Dict]): Дополнительные метаданные сообщения.
    """
    
    role: str = Field(
        ...,
        description="Роль отправителя сообщения (user_proxy, assistant, agent)"
    )
    
    content: str = Field(
        ...,
        description="Основное содержание сообщения (задача, результат, описание и т.д.)"
    )
    
    metadata: Optional[Dict] = Field(
        default_factory=dict,
        description="Дополнительные метаданные сообщения (task_id, timestamp, и т.д.)"
    )
    
    class Config:
        """Конфигурация модели Pydantic."""
        json_schema_extra = {
            "example": {
                "role": "user_proxy",
                "content": "Напишите функцию для вычисления факториала",
                "metadata": {
                    "task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "priority": "high"
                }
            }
        }