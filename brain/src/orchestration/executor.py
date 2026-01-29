import asyncio
import logging
import os
import json
from agents.agent_manager import AgentManager
from agents.parser import parse_code_blocks
from tools import tool_registry
from core.logging import LogContext


# Тактик - реализует паттерн State Machine для выполнения плана
class TaskExecutor:
    """
    Исполнитель задач (Тактик) с использованием паттерна State Machine.
    
    Класс реализует паттерн "State Machine" (конечный автомат) из архитектуры LangGraph.
    Строит граф выполнения, где каждый узел (node) — это функция-обработчик,
    а ребра (edges) — это переходы между ними. Это позволяет организовать
    последовательное и контролируемое выполнение задач.
    
    Адаптация из LangGraph:
        - Использование графа для описания потока выполнения
        - Регистрация узлов (nodes) как обработчиков состояний
        - Структурированные переходы между узлами
        - Надежная обработка результатов выполнения
    
    Роль "Тактика":
        - Получение плана от "Стратега"
        - Последовательное выполнение шагов плана
        - Координация работы агентов через AgentManager
        - Управление состоянием выполнения задачи
    
    Attributes:
        agent_manager (AgentManager): Менеджер для управления агентами.
        graph (dict): Граф выполнения в виде словаря узлов.
        logger (logging.Logger): Логгер для записи операций.
    """
    
    def __init__(self):
        """
        Инициализирует исполнителя задач и строит граф выполнения.
        
        Создает экземпляр AgentManager для управления Docker-агентами
        и регистрирует узлы (nodes) графа выполнения.
        """
        self.logger = logging.getLogger(__name__)
        
        # Логирование начала инициализации
        self.logger.info("TaskExecutor: Инициализация...")
        
        try:
            self.agent_manager = AgentManager()
            self.docker_available = True
            
            # Регистрация узлов графа (имитация LangGraph)
            # Каждый ключ — имя узла, значение — функция-обработчик
            self.graph = {
                "execute_step": self.execute_step_node
            }
            
            self.logger.info("TaskExecutor: Инициализация завершена.")
        except Exception as e:
            self.logger.error(f"TaskExecutor: Ошибка при инициализации: {str(e)}")
            self.agent_manager = None
            self.docker_available = False
            self.graph = {}
            self.logger.warning("TaskExecutor: Инициализация завершена без Docker (ограниченный режим)")
    
    async def process_llm_response(self, response_text, task_id: str):
        """
        Основной метод для обработки ответа LLM с архитектурой "Переключателя".
        
        Реализует гибридный подход: проверяет, содержит ли ответ вызов инструментов
        (MemGPT-style) или блоки кода (open-interpreter-style), и выполняет соответствующую логику.
        
        Args:
            response_text (str): Ответ от LLM (план или код).
            task_id (str): UUID задачи.
        
        Returns:
            str: Результат выполнения.
        """
        self.logger.info(f"TaskExecutor: Обработка ответа LLM для задачи {task_id}")
        
        # Set task context for logging
        LogContext.set("task_id", task_id)
        
        try:
            # Если response_text - список tool_call'ов, выполняем последовательно
            if isinstance(response_text, list):
                self.logger.info(f"TaskExecutor: Получен список из {len(response_text)} tool_call'ов")
                results = []
                for i, tool_call in enumerate(response_text):
                    self.logger.info(f"TaskExecutor: Выполнение шага {i+1}: {tool_call}")
                    try:
                        tool_name = tool_call["tool_name"]
                        arguments = tool_call["arguments"]
                        
                        result = await tool_registry.execute_tool(tool_name, **arguments)
                        results.append(result)
                        self.logger.info(f"TaskExecutor: Шаг {i+1} выполнен: {result}")
                            
                    except Exception as e:
                        self.logger.error(f"TaskExecutor: Ошибка на шаге {i+1}: {e}")
                        results.append({"error": str(e)})
                
                return json.dumps(results)
            
            # Иначе обрабатываем как строку
            self.logger.debug(f"TaskExecutor: Ответ LLM: {response_text[:200]}...")
            
            # Переключатель: проверка на вызов инструментов (MemGPT-style)
            try:
                parsed_json = json.loads(response_text.strip())
                if isinstance(parsed_json, dict) and "tool_calls" in parsed_json:
                    # TODO: Реализовать логику вызова инструментов в будущем
                    self.logger.info("TaskExecutor: Обнаружен вызов инструментов (MemGPT-mode) - пропуск")
                    
                    # Публикация события завершения выполнения
                    if self.event_dispatcher:
                        await self.event_dispatcher.complete_task(task_id)
                    
                    return "Инструменты пока не реализованы. Используйте режим кода."
            except json.JSONDecodeError:
                # Не JSON - продолжаем к режиму кода
                pass
            
            # Проверка на одиночный tool call в формате JSON
            try:
                tool_call = json.loads(response_text.strip())
                print(f"DEBUG: Распарсили tool call: {tool_call}")
                if isinstance(tool_call, dict) and "tool" in tool_call:
                    # Публикация события начала шага
                    if self.event_dispatcher:
                        await self.event_dispatcher.publish_event(
                            task_id, "STEP_STARTED", {"step": 1, "tool_call": tool_call}
                        )
                    
                    # Выполнение инструмента
                    self.logger.info(f"TaskExecutor: Выполнение инструмента: {tool_call}")
                    tool_name = tool_call.pop("tool")
                    print(f"DEBUG: tool_name={tool_name}, tool_call={tool_call}")
                    
                    # Публикация события вызова инструмента
                    if self.event_dispatcher:
                        await self.event_dispatcher.publish_event(
                            task_id, "TOOL_CALLED", {"tool_name": tool_name, "arguments": tool_call}
                        )
                    
                    result = await tool_registry.execute_tool(tool_name, **tool_call)
                    print(f"DEBUG: Результат выполнения: {result}")
                    
                    # Публикация события завершения шага
                    if self.event_dispatcher:
                        await self.event_dispatcher.publish_event(
                            task_id, "STEP_COMPLETED", {"step": 1, "result": result}
                        )
                        await self.event_dispatcher.complete_task(task_id)
                    
                    return json.dumps(result)
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}")
                # Не tool call - продолжаем к режиму кода
                pass
            
            # Режим кода: передача всего ответа агенту для последовательного выполнения
            self.logger.info("TaskExecutor: Передача всего ответа LLM агенту для выполнения")
            
            # Публикация события начала выполнения агента
            if self.event_dispatcher:
                await self.event_dispatcher.publish_event(
                    task_id, "AGENT_EXECUTION_STARTED", {"prompt_length": len(response_text)}
                )
            
            try:
                # Передаем весь ответ агенту
                result = await self.agent_manager.execute_step({"prompt": response_text}, task_id)
                self.logger.info(f"TaskExecutor: Агент выполнил задачу, результат: {result[:200]}...")
                
                # Публикация события завершения выполнения
                if self.event_dispatcher:
                    await self.event_dispatcher.publish_event(
                        task_id, "AGENT_EXECUTION_COMPLETED", {"result_length": len(result)}
                    )
                    await self.event_dispatcher.complete_task(task_id)
                
                return result
            except Exception as e:
                self.logger.error(f"TaskExecutor: Ошибка при передаче агенту: {e}")
                
                # Публикация события ошибки
                if self.event_dispatcher:
                    await self.event_dispatcher.fail_task(task_id, str(e))
                
                return f"Ошибка выполнения: {e}"
        
        except Exception as e:
            self.logger.error(f"TaskExecutor: Критическая ошибка в process_llm_response: {e}")
            
            # Публикация события критической ошибки
            if self.event_dispatcher:
                await self.event_dispatcher.fail_task(task_id, str(e))
            
            return f"Критическая ошибка выполнения: {e}"
    
    async def execute_step_node(self, plan):
        """
        Узел графа для выполнения отдельного шага плана.
        
        Это функция-узел в State Machine. Она извлекает информацию
        о агенте и задаче из плана и отправляет их на выполнение
        через AgentManager.
        
        Args:
            plan: Параметр плана (может быть dict или str для совместимости)
        
        Returns:
            str: Результат выполнения шага от агента.
        
        Notes:
            - Это узел State Machine, вызываемый из execute_plan
            - Получает данные через параметр plan
            - Результат возвращается для обработки в следующем узле
        """
        # Обработка разных типов plan для совместимости
        if isinstance(plan, str):
            # Если plan - строка, используем её как задачу напрямую
            task = plan
        elif isinstance(plan, dict):
            # Извлечение агента и задачи из аргументов плана
            arguments = plan.get('arguments', {})
            agent = arguments.get('agent')
            task = arguments.get('task')
        else:
            return f"Ошибка: неподдерживаемый тип plan: {type(plan)}"
        
        try:
            # Отправка задачи агенту через AgentManager
            result = await self.agent_manager.execute_step({"prompt": task})
        except Exception as e:
            self.logger.error(f"Ошибка в execute_step_node: {e}")
            result = f"Ошибка выполнения: {e}"
        
        return result
    
    async def execute_plan(self, plan: str, task_id: str):
        """
        Устаревший метод для совместимости. Перенаправляет на process_llm_response.
        
        Args:
            plan (str): План в виде строки (теперь с markdown блоками).
            task_id (str): UUID задачи.
        
        Returns:
            str: Результат выполнения.
        """
        self.logger.info(f"TaskExecutor: execute_plan вызван для задачи {task_id}, перенаправление на process_llm_response")
        try:
            return await self.process_llm_response(plan, task_id)
        except Exception as e:
            self.logger.error(f"TaskExecutor: Ошибка в execute_plan: {e}")
            raise