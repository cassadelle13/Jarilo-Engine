"""
Смотритель: Централизованный механизм обработки ошибок для асинхронных операций.

Этот модуль предоставляет декоратор @watch для надежной обработки исключений
в асинхронных функциях FastAPI-приложения.
"""

import logging
import traceback
from typing import Any, Tuple, Optional, Callable, Awaitable
from functools import wraps

logger = logging.getLogger(__name__)


def watch(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Tuple[Optional[Any], Optional[Exception]]]]:
    """
    Асинхронный декоратор для обработки исключений.

    Оборачивает async функцию в try-except, логирует ошибки и возвращает кортеж (result, error).
    Если ошибки нет, возвращает (result, None).
    Если ошибка есть, возвращает (None, exception).

    Args:
        func: Асинхронная функция для декорирования.

    Returns:
        Декорированная функция, возвращающая кортеж (result, error).
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Tuple[Optional[Any], Optional[Exception]]:
        logger.debug(f"Watcher: Вызываем {func.__name__}")
        print(f"Смотритель: Вызываем {func.__name__}")
        try:
            logger.debug(f"Watcher: Вход в try для {func.__name__}")
            result = await func(*args, **kwargs)
            logger.debug(f"Watcher: {func.__name__} выполнен успешно")
            print(f"Смотритель: {func.__name__} выполнен успешно")
            return result, None
        except Exception as e:
            logger.error(f"Watcher: Перехвачена ошибка в {func.__name__}: {e}")
            logger.error(f"Watcher: Traceback: {traceback.format_exc()}")
            print(f"Смотритель: Перехвачена ошибка в {func.__name__}: {e}")
            return None, e

    return wrapper