from fastapi import APIRouter, Depends, HTTPException
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from workspace.state_manager import StateManager
from orchestration.simple_integrated_graph import get_simple_integrated_orchestrator
from api.dependencies import get_state_manager, get_llm
from .schemas import TaskCreate, Task
import logging
import traceback
from core.logging import LogContext

# Import streaming endpoints
from .streaming_endpoints import router as streaming_router

logger = logging.getLogger(__name__)

router = APIRouter()

# Include streaming router for real-time features
router.include_router(streaming_router, tags=["streaming"])

# Include secrets router
# router.include_router(secrets_router, tags=["secrets"])


@router.get("/tasks/")
async def health_check():
    """
    Health check endpoint for Jarilo API
    """
    return {"status": "healthy", "service": "Jarilo AI", "version": "1.0.0"}


@router.post("/tasks/", response_model=None)
async def create_task(
    task_in: TaskCreate,
    state_manager: StateManager = Depends(get_state_manager),
    llm = Depends(get_llm),
):
    print("=== CREATE_TASK FUNCTION START ===")
    """
    Создает задачу и запускает умную оркестрацию через IntegratedOrchestrator:
      1. Анализирует сложность задачи
      2. Выбирает оптимальную стратегию (LangGraph/PlanExecute/Hybrid)
      3. Выполняет задачу с интеллектуальной обработкой ошибок
      4. Сохраняет результаты в базу данных
      5. Возвращает полный результат с метаданными
    
    Использует Dependency Injection для получения сервисов: StateManager, LLM.
    """
    print("=== ВХОД В CREATE_TASK ===")
    logger.info("=== ВХОД В CREATE_TASK ===")
    try:
        logger.debug("create_task: Начало выполнения")
        print(f"Эндпоинт create_task вызван с prompt: {task_in.prompt}")
        
        logger.debug("create_task: Шаг 1 - Создание задачи")
        db_task = await state_manager.create_task(prompt=task_in.prompt)
        logger.debug(f"create_task: Задача создана: {db_task['id']}")

        logger.debug("create_task: Шаг 2 - Запуск Integrated Orchestrator")
        print("Запускаем Integrated Orchestrator для умной оркестрации задачи")

        # Set task context for logging
        LogContext.set("task_id", db_task["id"])

        # Получаем упрощенный оркестратор
        orchestrator = get_simple_integrated_orchestrator(llm)
        
        # Запускаем умное выполнение
        logger.info("Запуск orchestrator.execute")
        print("=== ORCHESTRATOR.EXECUTE STARTED ===")
        print(f"Task description: {task_in.prompt}")
        
        execution_result = await orchestrator.execute(task_in.prompt)
        
        print(f"=== ORCHESTRATOR.EXECUTE FINISHED ===")
        print(f"Результат выполнения: {execution_result}")
        logger.debug(f"create_task: Оркестратор завершил выполнение: {execution_result}")

        logger.debug("create_task: Шаг 3 - Создание финального результата")
        
        # Извлекаем результаты
        strategy_used = execution_result.get("strategy", "unknown")
        final_result = execution_result.get("final_result", [])
        metadata = execution_result.get("metadata", {})
        execution_time = execution_result.get("execution_time", 0)
        
        # Создаем улучшенный объект Task
        final_task = {
            "id": db_task["id"],
            "status": "completed" if not execution_result.get("error") else "failed",
            "prompt": task_in.prompt,
            "plan": execution_result.get("plan", []),
            "result": final_result if isinstance(final_result, list) else [str(final_result)],
            # НОВЫЕ ПОЛЯ ДЛЯ УЛУЧШЕННОГО ОПЫТА
            "strategy": strategy_used,
            "execution_time": execution_time,
            "complexity": execution_result.get("complexity", 0),
            "confidence": execution_result.get("confidence", 0),
            "metadata": metadata
        }
        
        # Сохраняем задачу с результатами в базу данных
        try:
            await state_manager.update_task_status(task_id=db_task["id"], new_status=final_task["status"])
            
            # Сохраняем план из финального состояния
            if execution_result.get("plan"):
                await state_manager.update_task_plan(task_id=db_task["id"], plan=execution_result["plan"])
            
            # Сохраняем результаты выполнения
            if final_result:
                for i, result in enumerate(final_result):
                    await state_manager.add_step_result(task_id=db_task["id"], result={
                        "step": {"description": f"Execution step {i+1} ({strategy_used})"},
                        "status": "completed", 
                        "output": result
                    })
            
            print(f"Задача сохранена в базу данных: {db_task['id']}")
            print(f"Метрики: стратегия={strategy_used}, время={execution_time:.2f}s, уверенность={execution_result.get('confidence', 0):.2f}")
        except Exception as save_error:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Не удалось сохранить в базу: {save_error}")
        
        print(f"Финальная задача создана: {final_task}")
        logger.debug("create_task: Завершение выполнения")
        
        # Возвращаем Task объект
        from api.v1 import schemas
        try:
            task_obj = Task(**final_task)
            print(f"Создан Task объект: status={task_obj.status}, strategy={strategy_used}")
            return task_obj
        except Exception as schema_error:
            print(f"Ошибка в Task: {schema_error}")
            return final_task
            
    except Exception as e:
        logger.error(f"create_task: Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        print(f"Исключение в create_task: {e}")
        # Возвращаем задачу с ошибкой
        return Task(
            id=db_task["id"] if 'db_task' in locals() else "unknown",
            status="failed",
            prompt=task_in.prompt,
            plan=[],
            result=[f"Ошибка выполнения: {str(e)}"],
            strategy="error",
            execution_time=0,
            complexity=0,
            confidence=0,
            metadata={"error": True}
        )


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task_status(
    task_id: str,
    state_manager: StateManager = Depends(get_state_manager)
):
    """
    Получает информацию о задаче по её ID.

    Возвращает полную информацию о задаче, включая её текущий статус,
    план и результаты выполнения. Если задача не найдена,
    возвращает ошибку 404 Not Found.
    
    Args:
        task_id (str): UUID уникальный идентификатор задачи.
        state_manager (StateManager): Менеджер состояния из DI.
    
    Returns:
        Task: Полная информация о задаче.
    
    Raises:
        HTTPException: 404 если задача не найдена.
    """
    task = await state_manager.get_task(task_id=task_id)
    
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    
    return task