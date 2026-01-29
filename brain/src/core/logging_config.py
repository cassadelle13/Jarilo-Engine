import logging.config
import sys


# Production-ready конфигурация логирования для Jarilo (адаптирована из FastAPI best practices)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "jarilo.log",
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        },
        "jarilo": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}


def setup_logging():
    """
    Инициализирует систему логирования приложения Jarilo.
    
    Применяет конфигурацию логирования из словаря LOGGING_CONFIG.
    Должна быть вызвана один раз при запуске приложения.
    
    Конфигурация включает:
        - Форматеры для структурирования логов
        - Хендлеры для вывода в консоль и файл
        - Логгеры для различных компонентов (uvicorn, jarilo и т.д.)
    
    Использование:
        >>> from core.logging_config import setup_logging
        >>> setup_logging()
        >>> logger = logging.getLogger("jarilo")
        >>> logger.info("Приложение запущено")
    
    Notes:
        - Логирование конфигурируется один раз при запуске
        - Все существующие логгеры переконфигурируются
        - Логи выводятся в консоль (stdout) и в файл jarilo.log
    """
    logging.config.dictConfig(LOGGING_CONFIG)