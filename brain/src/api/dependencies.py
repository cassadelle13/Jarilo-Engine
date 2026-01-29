"""
Централизованный модуль зависимостей для Jarilo (Dependency Injection).

Этот файл предоставляет функции-провайдеры для получения сервисов из app.state.
Инициализация сервисов происходит в lifespan main.py.
"""

from workspace.state_manager import StateManager
from orchestration import compiled_graph
from core.config import settings
from orm.db import get_db_session
from fastapi import Request
from langchain_openai import ChatOpenAI
import os
import logging

logger = logging.getLogger(__name__)


def get_state_manager(request: Request) -> StateManager:
    """
    Провайдер StateManager для Dependency Injection.

    Возвращает экземпляр StateManager из app.state.
    """
    # Если StateManager не инициализирован, создаем новый
    if not hasattr(request.app.state, 'state_manager'):
        request.app.state.state_manager = StateManager()
        logger.info("StateManager создан и сохранен в app.state")
    
    return request.app.state.state_manager


def get_compiled_graph(request: Request):
    """
    Провайдер CompiledGraph для Dependency Injection.

    Возвращает скомпилированный LangGraph из app.state.
    """
    return request.app.state.compiled_graph


def get_db_session():
    """
    Провайдер AsyncSession для Dependency Injection.

    Возвращает асинхронную сессию базы данных для работы с моделями.
    """
    return get_db_session


def get_llm(request: Request):
    """
    Провайдер LLM для Dependency Injection.

    Возвращает экземпляр ChatOpenAI для работы с языковой моделью.
    """
    # Проверяем, есть ли LLM в app.state
    if hasattr(request.app.state, 'llm'):
        return request.app.state.llm
    
    # Создаем новый экземпляр если нет в state
    api_key = (getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY"))
    if not api_key or api_key.startswith("your_val") or api_key == "test-key":
        logger.warning("OPENAI_API_KEY не настроен. Используем тестовый режим.")
        # Возвращаем mock LLM для тестов
        return MockLLM()
    
    try:
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=api_key
        )
        logger.info("LLM инициализирован успешно")
        return llm
    except Exception as e:
        logger.error(f"Ошибка инициализации LLM: {e}")
        return MockLLM()


class MockLLM:
    """
    Mock LLM для тестирования когда OpenAI API недоступен.
    """
    async def ainvoke(self, messages):
        """Mock invoke method."""
        return "Mock response: LLM not configured. Please set OPENAI_API_KEY environment variable."
    
    def invoke(self, messages):
        """Mock invoke method."""
        return "Mock response: LLM not configured. Please set OPENAI_API_KEY environment variable."