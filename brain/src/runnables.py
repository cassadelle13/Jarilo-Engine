"""
Runnable для выполнения задач с поддержкой стриминга через LangServe.

Этот модуль инкапсулирует логику выполнения задач в LangChain Runnable,
что позволяет использовать LangServe для автоматического создания эндпоинтов
с потоковой передачей событий.
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List

from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel

from orchestration.graph import compiled_graph
from workspace.state_manager import StateManager
from core.logging import LogContext

logger = logging.getLogger(__name__)


class TaskInput(BaseModel):
    """Входные данные для runnable."""
    prompt: str


class TaskOutput(BaseModel):
    """Выходные данные runnable."""
    task_id: str
    status: str
    prompt: str
    plan: Any
    result: Any


class TaskRunnable(Runnable):
    """
    Runnable для выполнения задач с потоковой передачей событий.

    Инкапсулирует полный цикл: планирование -> исполнение -> результат.
    Поддерживает асинхронный стрим промежуточных событий.
    """

    input_type = TaskInput
    output_type = TaskOutput

    def __init__(self):
        """Инициализирует компоненты для выполнения задач."""
        self.logger = logging.getLogger(__name__)
        self.state_manager = StateManager()
        self.graph = compiled_graph

    def invoke(self, input_data: TaskInput, config: RunnableConfig = None) -> TaskOutput:
        """
        Синхронное выполнение задачи.

        Args:
            input_data: Входные данные с промптом
            config: Конфигурация runnable

        Returns:
            Результат выполнения задачи
        """
        import asyncio
        return asyncio.run(self.ainvoke(input_data, config))

    def stream(self, input_data: TaskInput, config: RunnableConfig = None):
        """
        Синхронный стрим.

        Args:
            input_data: Входные данные
            config: Конфигурация

        Yields:
            События
        """
        import asyncio
        async_gen = self.astream(input_data, config)
        try:
            while True:
                yield asyncio.run(async_gen.__anext__())
        except StopAsyncIteration:
            pass

    def transform(self, input_data: TaskInput, config: RunnableConfig = None):
        """
        Трансформация входных данных.

        Args:
            input_data: Входные данные
            config: Конфигурация

        Returns:
            Трансформированные данные
        """
        return input_data

    def batch(self, inputs: list[TaskInput], config: RunnableConfig = None):
        """
        Пакетная обработка.

        Args:
            inputs: Список входных данных
            config: Конфигурация

        Returns:
            Список результатов
        """
        return [self.invoke(input_data, config) for input_data in inputs]

    async def abatch(self, inputs: list[TaskInput], config: RunnableConfig = None):
        """
        Асинхронная пакетная обработка.

        Args:
            inputs: Список входных данных
            config: Конфигурация

        Returns:
            Список результатов
        """
        return [await self.ainvoke(input_data, config) for input_data in inputs]

    def stream_log(self, input_data: TaskInput, config: RunnableConfig = None):
        """
        Стрим с логированием.

        Args:
            input_data: Входные данные
            config: Конфигурация

        Yields:
            Логированные события
        """
        for event in self.stream(input_data, config):
            yield event

    async def astream_log(self, input_data: TaskInput, config: RunnableConfig = None):
        """
        Асинхронный стрим с логированием.

        Args:
            input_data: Входные данные
            config: Конфигурация

        Yields:
            Логированные события
        """
        async for event in self.astream(input_data, config):
            yield event

    async def astream_events(self, input_data: TaskInput, config: RunnableConfig = None):
        """
        Асинхронный стрим событий.

        Args:
            input_data: Входные данные
            config: Конфигурация

        Yields:
            События
        """
        async for event in self.astream(input_data, config):
            yield event
    async def ainvoke(self, input_data: TaskInput, config: RunnableConfig = None) -> TaskOutput:
        """
        Асинхронное выполнение задачи через LangGraph.

        Args:
            input_data: Входные данные с промптом
            config: Конфигурация runnable

        Returns:
            Результат выполнения задачи
        """
        prompt = input_data.prompt
        self.logger.info(f"TaskRunnable: Выполнение задачи с промптом: {prompt[:50]}...")

        # Создаем задачу
        db_task = await self.state_manager.create_task(prompt=prompt)

        # Set task context for logging
        LogContext.set("task_id", db_task["id"])

        # Run graph
        initial_state = {
            "task_description": prompt,
            "plan": None,  # Изменено с [] на None для правильной логики
            "critique": "",
            "tool_calls": [],
            "tool_results": [],
            "replan_attempts": 0
        }
        final_state = await self.graph.ainvoke(initial_state)

        # Update task status
        await self.state_manager.update_task_status(task_id=db_task["id"], new_status="execution_completed")
        await self.state_manager.update_task_plan(task_id=db_task["id"], plan=final_state["plan"])

        if final_state["tool_results"]:
            await self.state_manager.add_step_result(
                task_id=db_task["id"],
                result={"step": {"description": "Execution results"}, "status": "completed", "output": final_state["tool_results"]}
            )

        return TaskOutput(
            task_id=db_task["id"],
            status="completed",
            prompt=prompt,
            plan=final_state["plan"],
            result=final_state["tool_results"]
        )

    async def astream(self, input_data: Dict[str, Any], config: RunnableConfig = None) -> AsyncIterator[Dict[str, Any]]:
        """
        Асинхронный стрим выполнения задачи с промежуточными событиями.

        Args:
            input_data: Данные с промптом задачи {"prompt": "текст"}
            config: Конфигурация runnable

        Yields:
            Промежуточные события выполнения
        """
        prompt = input_data.get("prompt", "")
        if not prompt:
            raise ValueError("Prompt is required")

        self.logger.info(f"TaskRunnable: Стрим выполнения задачи: {prompt[:50]}...")

        # Создаем задачу
        db_task = await self.state_manager.create_task(prompt=prompt)
        yield {"event": "task_created", "task_id": db_task["id"], "prompt": prompt}

        # Set task context for logging
        LogContext.set("task_id", db_task["id"])

        # Планируем
        yield {"event": "planning_started", "task_id": db_task["id"]}
        plan = await self.planner.create_plan(prompt=prompt)
        await self.state_manager.update_task_status(task_id=db_task["id"], new_status="planning_completed")
        await self.state_manager.update_task_plan(task_id=db_task["id"], plan=plan)
        yield {"event": "planning_completed", "task_id": db_task["id"], "plan": plan}

        # Выполняем с событиями
        yield {"event": "execution_started", "task_id": db_task["id"]}

        # Если план - список tool_call'ов, стриммим каждый шаг
        if isinstance(plan, list):
            for i, tool_call in enumerate(plan):
                yield {"event": "step_started", "task_id": db_task["id"], "step": i+1, "tool_call": tool_call}

                try:
                    tool_name = tool_call["tool_name"]
                    arguments = tool_call["arguments"]
                    result = await self.executor._execute_tool_call(tool_name, arguments)  # Предполагаем метод

                    yield {"event": "step_completed", "task_id": db_task["id"], "step": i+1, "result": result}

                except Exception as e:
                    yield {"event": "step_failed", "task_id": db_task["id"], "step": i+1, "error": str(e)}

        # Финальный результат
        result = await self.executor.process_llm_response(plan, db_task["id"])
        await self.state_manager.update_task_status(task_id=db_task["id"], new_status="execution_completed")

        if result:
            await self.state_manager.add_step_result(
                task_id=db_task["id"],
                result={"step": {"description": "Final execution result"}, "status": "completed", "output": result}
            )

        yield {"event": "execution_completed", "task_id": db_task["id"], "result": result}


# Экземпляр runnable для использования в LangServe
task_runnable = TaskRunnable()