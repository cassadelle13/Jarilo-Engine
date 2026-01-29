from pydantic import BaseModel
from typing import List, Dict, Any, Union


# Схемы Pydantic для валидации входящих данных и форматирования ответов


class TaskCreate(BaseModel):
    """
    Схема для создания новой задачи.
    
    Используется для валидации входящих данных от клиента при создании задачи.
    
    Поля:
        prompt (str): Описание задачи или инструкций, предоставленных пользователем.
    """
    prompt: str


class Task(BaseModel):
    """
    Улучшенная схема представления задачи с поддержкой AI Agent архитектуры.
    
    Включает метаданные задачи, сформированный план, результаты выполнения
    и дополнительную информацию о стратегии выполнения.
    
    Поля:
        id (str): Уникальный идентификатор задачи.
        status (str): Текущий статус задачи (created, planning, executing, completed, failed).
        prompt (str): Исходный промпт/описание задачи.
        plan (Any): Структурированный план выполнения.
        result (Union[List[str], None]): Результат выполнения задачи.
        strategy (str): Использованная стратегия выполнения (langgraph, plan_execute, hybrid).
        execution_time (float): Время выполнения в секундах.
        complexity (int): Оценка сложности задачи (1-10).
        confidence (float): Уверенность в выполнении (0-1).
        metadata (Dict[str, Any]): Дополнительные метаданные выполнения.
    """
    id: str
    status: str
    prompt: str
    plan: Any
    result: Union[List[str], None] = None
    
    # НОВЫЕ ПОЛЯ ДЛЯ УЛУЧШЕННОГО ОПЫТА
    strategy: str = "unknown"
    execution_time: float = 0.0
    complexity: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = {}