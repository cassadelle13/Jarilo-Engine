# ...existing code...
import sys
import os
# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Временное решение для logging
import logging
jarilo_logger = logging.getLogger('jarilo')
jarilo_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
jarilo_logger.addHandler(handler)

def setup_logging():
    pass

# Основные импорты FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse

from api.v1 import endpoints

# Import LangServe
try:
    from langserve import add_routes
    from runnables import task_runnable
    jarilo_logger.info("LangServe imported successfully")
except Exception as e:
    jarilo_logger.error(f"Failed to import LangServe: {e}")
    add_routes = None
    task_runnable = None

# Import secrets router
try:
    from api.v1.secrets_router import router as secrets_router
    jarilo_logger.info("secrets_router imported successfully")
except Exception as e:
    jarilo_logger.error(f"Failed to import secrets_router: {e}")
    secrets_router = None

# Import bootstrap router
try:
    from api.v1.bootstrap_router import router as bootstrap_router
    jarilo_logger.info("bootstrap_router imported successfully")
except Exception as e:
    jarilo_logger.error(f"Failed to import bootstrap_router: {e}")
    bootstrap_router = None

from api.middleware import ExceptionHandlerMiddleware, RequestLoggingMiddleware
from api.v1.health_router import router as health_router
from orm import db_manager
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    jarilo_logger.info("Приложение запускается...")
    try:
        # Инициализация базы данных
        await db_manager.init_db()
        jarilo_logger.info("Database initialized successfully")

        # Инициализация StateManager
        from workspace.state_manager import StateManager
        app.state.state_manager = StateManager()
        jarilo_logger.info("StateManager initialized successfully")

        # Инициализация ToolRegistry
        from tools.registry import ToolRegistry
        app.state.tool_registry = ToolRegistry()
        jarilo_logger.info("ToolRegistry initialized successfully")

        # Инициализация LangGraph
        try:
            from orchestration import compiled_graph
            app.state.compiled_graph = compiled_graph
            jarilo_logger.info("LangGraph initialized successfully")
        except Exception as e:
            jarilo_logger.error(f"Failed to initialize LangGraph: {e}", exc_info=True)
            app.state.compiled_graph = None

        yield
        jarilo_logger.info("Приложение завершается нормально")
    except Exception as e:
        jarilo_logger.error(f"Приложение завершается с ошибкой: {e}", exc_info=True)
        raise
    finally:
        # Закрытие базы данных
        await db_manager.close_db()
        jarilo_logger.info("Database connection closed")

try:
    # Создание экземпляра FastAPI приложения
    app = FastAPI(title="Jarilo Brain", lifespan=lifespan)

    # Добавление CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*", "http://localhost:3002", "http://localhost:8003"],  # Разрешить все источники + фронтенд
        allow_credentials=True,
        allow_methods=["*"],  # Разрешить все методы
        allow_headers=["*"],  # Разрешить все заголовки
    )

    # Добавление middleware
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Подключение маршрутов API

    app.include_router(endpoints.router, prefix="/api/v1", tags=["API v1"])

    if secrets_router:
        app.include_router(secrets_router, prefix="/api/v1", tags=["secrets"])
    else:
        jarilo_logger.warning("secrets_router not available")

    if bootstrap_router:
        app.include_router(bootstrap_router, prefix="/api/v1", tags=["bootstrap"])
    else:
        jarilo_logger.warning("bootstrap_router not available")

    # Health check routes
    app.include_router(health_router, prefix="/api/v1", tags=["health"])

    from api.v1.workflow_generation import router as workflow_router
    app.include_router(workflow_router, tags=["workflow"])

    # LangServe routes for streaming tasks
    if False and add_routes and task_runnable:  # ВРЕМЕННО ОТКЛЮЧЕНО
        add_routes(app, task_runnable, path="/api/v1/tasks/runnable")
        jarilo_logger.info("LangServe routes added")
    else:
        jarilo_logger.warning("LangServe disabled for debugging")

    jarilo_logger.info("Роутеры зарегистрированы успешно")

    # Простой тестовый эндпоинт
    @app.get("/api/v1/test-secrets")
    async def test_secrets():
        jarilo_logger.info("Тестовый эндпоинт вызван")
        return {"message": "Secrets endpoint works", "status": "ok"}

    jarilo_logger.info("Тестовый эндпоинт добавлен")
    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    @app.post("/test")
    async def test_endpoint(data: dict):
        return {"received": data}

    jarilo_logger.info(f"Все маршруты зарегистрированы: {[route.path for route in app.routes]}")

except Exception as e:
    jarilo_logger.error(f"ОШИБКА при создании FastAPI приложения: {e}", exc_info=True)
    raise

# Глобальный обработчик исключений
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    jarilo_logger.error(f"Необработанное исключение: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Внутренняя ошибка сервера: {str(exc)}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ...existing code...