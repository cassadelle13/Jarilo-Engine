"""
🚀 Plan Execute Agent - Умный AI агент с архитектурой Plan and Execute

Вдохновлено лучшими практиками n8n, но написано с нуля для Jarilo:
- Адаптивное планирование
- Интеллектуальная обработка ошибок
- Валидация каждого шага
- Самообучение и оптимизация
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseLanguageModel

# Настройка логирования
logger = logging.getLogger(__name__)

class StepStatus(Enum):
    """Статусы выполнения шагов"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"

class StepPriority(Enum):
    """Приоритеты шагов"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Step:
    """Шаг выполнения плана"""
    id: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    priority: StepPriority = StepPriority.MEDIUM
    dependencies: List[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 30
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    confidence: float = 0.8
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class ExecutionPlan:
    """План выполнения"""
    id: str
    task_description: str
    steps: List[Step]
    estimated_time: int
    confidence: float
    created_at: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ExecutionResult:
    """Результат выполнения плана"""
    plan_id: str
    success: bool
    completed_steps: List[Step]
    failed_steps: List[Step]
    total_time: float
    final_result: Optional[Any] = None
    error_summary: Optional[str] = None
    performance_metrics: Dict[str, Any] = None

class BaseTool(ABC):
    """Базовый класс для инструментов"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Выполнить инструмент"""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Валидировать параметры"""
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Получить схему параметров"""
        pass

class ToolRegistry:
    """Реестр инструментов"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_usage_stats: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_tool(self, tool: BaseTool):
        """Зарегистрировать инструмент"""
        self.tools[tool.name] = tool
        self.tool_usage_stats[tool.name] = 0
        self.logger.info(f"✅ Инструмент '{tool.name}' зарегистрирован")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Получить инструмент"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """Получить список инструментов"""
        return list(self.tools.keys())
    
    def get_tool_stats(self) -> Dict[str, int]:
        """Получить статистику использования"""
        return self.tool_usage_stats.copy()
    
    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Tuple[Any, float]:
        """Выполнить инструмент с замером времени"""
        if name not in self.tools:
            raise ValueError(f"Инструмент '{name}' не найден")
        
        tool = self.tools[name]
        
        # Валидация параметров
        if not tool.validate_parameters(parameters):
            raise ValueError(f"Неверные параметры для инструмента '{name}'")
        
        # Выполнение с замером времени
        start_time = time.time()
        try:
            result = await tool.execute(parameters)
            execution_time = time.time() - start_time
            
            # Обновление статистики
            self.tool_usage_stats[name] += 1
            
            self.logger.info(f"✅ Инструмент '{name}' выполнен за {execution_time:.2f}s")
            return result, execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Инструмент '{name}' завершился с ошибкой: {e}")
            raise e

class PlanExecuteAgent:
    """🚀 Plan Execute Agent - основной класс агента"""
    
    def __init__(self, llm: BaseLanguageModel, tool_registry: ToolRegistry):
        self.llm = llm
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(__name__)
        self.execution_history: List[ExecutionResult] = []
        
        # Настройки агента
        self.max_planning_attempts = 3
        self.max_execution_time = 300  # 5 минут
        self.confidence_threshold = 0.7
        
    async def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """🔍 Анализ задачи"""
        self.logger.info("🔍 Анализирую задачу...")
        
        system_prompt = """
        Ты - AI аналитик. Проанализируй задачу и определи:
        1. Тип задачи (данные, API, файлы, и т.д.)
        2. Необходимые инструменты
        3. Сложность (1-10)
        4. Предполагаемое время выполнения
        5. Возможные риски
        
        Ответ в формате JSON:
        {
            "task_type": "тип задачи",
            "required_tools": ["инструмент1", "инструмент2"],
            "complexity": 7,
            "estimated_time": 120,
            "risks": ["риск1", "риск2"],
            "success_probability": 0.8
        }
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Задача: {task_description}")
            ])
            
            # Парсинг JSON ответа
            analysis = json.loads(response.content)
            self.logger.info(f"✅ Анализ завершен: {analysis}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа: {e}")
            # Возвращаем анализ по умолчанию
            return {
                "task_type": "general",
                "required_tools": ["python"],
                "complexity": 5,
                "estimated_time": 60,
                "risks": ["unknown"],
                "success_probability": 0.6
            }
    
    async def create_plan(self, task_description: str, analysis: Dict[str, Any]) -> ExecutionPlan:
        """📋 Создание плана выполнения"""
        self.logger.info("📋 Создаю план выполнения...")
        
        available_tools = self.tool_registry.list_tools()
        required_tools = analysis.get("required_tools", [])
        
        # Фильтруем доступные инструменты
        usable_tools = [tool for tool in required_tools if tool in available_tools]
        
        system_prompt = f"""
        Ты - AI планировщик. Создай детальный план для задачи.
        
        Задача: {task_description}
        Анализ: {json.dumps(analysis, ensure_ascii=False)}
        
        Доступные инструменты: {usable_tools}
        
        Создай пошаговый план в формате JSON:
        {{
            "steps": [
                {{
                    "description": "Описание шага",
                    "tool": "название_инструмента",
                    "parameters": {{
                        "param1": "value1"
                    }},
                    "priority": "high|medium|low",
                    "dependencies": []
                }}
            ],
            "estimated_time": 120,
            "confidence": 0.8
        }}
        
        Требования:
        1. Каждый шаг должен быть конкретным и выполнимым
        2. Используй только доступные инструменты
        3. Укажи зависимости между шагами
        4. Оцени время и уверенность
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Создай план для этой задачи")
            ])
            
            plan_data = json.loads(response.content)
            
            # Создаем объекты Step
            steps = []
            for i, step_data in enumerate(plan_data["steps"]):
                step = Step(
                    id=f"step_{i+1}",
                    description=step_data["description"],
                    tool=step_data["tool"],
                    parameters=step_data["parameters"],
                    priority=StepPriority(step_data.get("priority", "medium"))
                )
                steps.append(step)
            
            plan = ExecutionPlan(
                id=f"plan_{int(time.time())}",
                task_description=task_description,
                steps=steps,
                estimated_time=plan_data["estimated_time"],
                confidence=plan_data["confidence"],
                created_at=time.time()
            )
            
            self.logger.info(f"✅ План создан: {len(steps)} шагов, уверенность: {plan.confidence}")
            return plan
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания плана: {e}")
            raise e
    
    async def validate_plan(self, plan: ExecutionPlan) -> Tuple[bool, List[str]]:
        """🔍 Валидация плана"""
        self.logger.info("🔍 Валидирую план...")
        
        issues = []
        
        # Проверяем инструменты
        for step in plan.steps:
            if step.tool not in self.tool_registry.list_tools():
                issues.append(f"Шаг {step.id}: инструмент '{step.tool}' не найден")
        
        # Проверяем зависимости
        step_ids = {step.id for step in plan.steps}
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    issues.append(f"Шаг {step.id}: зависимость '{dep}' не найдена")
        
        # Проверяем циклические зависимости
        if self._has_circular_dependencies(plan.steps):
            issues.append("Обнаружены циклические зависимости")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            self.logger.info("✅ План валидирован успешно")
        else:
            self.logger.warning(f"⚠️ План имеет проблемы: {issues}")
        
        return is_valid, issues
    
    def _has_circular_dependencies(self, steps: List[Step]) -> bool:
        """Проверка циклических зависимостей"""
        # Простая реализация DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = next((s for s in steps if s.id == step_id), None)
            if step:
                for dep in step.dependencies:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        for step in steps:
            if step.id not in visited:
                if has_cycle(step.id):
                    return True
        
        return False
    
    async def improve_plan(self, plan: ExecutionPlan, issues: List[str]) -> ExecutionPlan:
        """🔧 Улучшение плана"""
        self.logger.info("🔧 Улучшаю план...")
        
        system_prompt = f"""
        Ты - AI оптимизатор. Улучти план на основе проблем.
        
        Текущий план: {json.dumps([asdict(step) for step in plan.steps], ensure_ascii=False)}
        Проблемы: {issues}
        
        Исправь проблемы и верни улучшенный план в том же формате.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Улучти этот план")
            ])
            
            improved_data = json.loads(response.content)
            
            # Создаем улучшенные шаги
            improved_steps = []
            for i, step_data in enumerate(improved_data["steps"]):
                step = Step(
                    id=f"step_{i+1}_improved",
                    description=step_data["description"],
                    tool=step_data["tool"],
                    parameters=step_data["parameters"],
                    priority=StepPriority(step_data.get("priority", "medium"))
                )
                improved_steps.append(step)
            
            improved_plan = ExecutionPlan(
                id=f"{plan.id}_improved",
                task_description=plan.task_description,
                steps=improved_steps,
                estimated_time=improved_data.get("estimated_time", plan.estimated_time),
                confidence=improved_data.get("confidence", plan.confidence),
                created_at=time.time()
            )
            
            self.logger.info("✅ План улучшен")
            return improved_plan
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка улучшения плана: {e}")
            return plan
    
    async def execute_step(self, step: Step) -> Tuple[bool, Any, float]:
        """⚡ Выполнение одного шага"""
        self.logger.info(f"⚡ Выполняю шаг: {step.description}")
        
        step.status = StepStatus.RUNNING
        start_time = time.time()
        
        try:
            result, execution_time = await self.tool_registry.execute_tool(
                step.tool, 
                step.parameters
            )
            
            step.status = StepStatus.SUCCESS
            step.result = result
            step.execution_time = execution_time
            
            self.logger.info(f"✅ Шаг выполнен успешно за {execution_time:.2f}s")
            return True, result, execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.execution_time = execution_time
            
            self.logger.error(f"❌ Шаг завершился с ошибкой: {e}")
            return False, None, execution_time
    
    async def retry_step(self, step: Step, alternative_approach: bool = False) -> Tuple[bool, Any, float]:
        """🔄 Повторное выполнение шага"""
        self.logger.info(f"🔄 Повторяю шаг: {step.description}")
        
        if step.retry_count >= step.max_retries:
            self.logger.warning(f"⚠️ Превышено максимальное количество повторов для шага {step.id}")
            return False, None, 0.0
        
        step.retry_count += 1
        step.status = StepStatus.RETRYING
        
        if alternative_approach:
            # Генерируем альтернативный подход
            alternative_params = await self.generate_alternative_approach(step)
            if alternative_params:
                step.parameters = alternative_params
                self.logger.info(f"🔄 Использую альтернативные параметры: {alternative_params}")
        
        return await self.execute_step(step)
    
    async def generate_alternative_approach(self, step: Step) -> Optional[Dict[str, Any]]:
        """🎯 Генерация альтернативного подхода"""
        system_prompt = f"""
        Ты - AI решатель проблем. Шаг завершился с ошибкой.
        
        Шаг: {step.description}
        Инструмент: {step.tool}
        Параметры: {step.parameters}
        Ошибка: {step.error}
        
        Предложи альтернативные параметры для выполнения этого шага.
        Верни JSON с новыми параметрами.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Предложи альтернативный подход")
            ])
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка генерации альтернативы: {e}")
            return None
    
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """🚀 Выполнение плана"""
        self.logger.info(f"🚀 Начинаю выполнение плана: {plan.id}")
        
        start_time = time.time()
        completed_steps = []
        failed_steps = []
        
        # Сортируем шаги по приоритету и зависимостям
        sorted_steps = self._sort_steps_by_priority_and_dependencies(plan.steps)
        
        for step in sorted_steps:
            # Проверяем зависимости
            if not self._check_dependencies(step, completed_steps):
                self.logger.warning(f"⚠️ Пропускаю шаг {step.id} - зависимости не выполнены")
                step.status = StepStatus.SKIPPED
                continue
            
            # Выполняем шаг
            success, result, execution_time = await self.execute_step(step)
            
            if success:
                completed_steps.append(step)
            else:
                # Пробуем повторить с альтернативным подходом
                retry_success, retry_result, retry_time = await self.retry_step(step, alternative_approach=True)
                
                if retry_success:
                    completed_steps.append(step)
                else:
                    failed_steps.append(step)
            
            # Проверяем таймаут
            if time.time() - start_time > self.max_execution_time:
                self.logger.warning("⚠️ Превышено максимальное время выполнения")
                break
        
        total_time = time.time() - start_time
        
        # Формируем результат
        result = ExecutionResult(
            plan_id=plan.id,
            success=len(failed_steps) == 0,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            total_time=total_time,
            final_result=self._combine_results(completed_steps),
            error_summary=self._generate_error_summary(failed_steps),
            performance_metrics={
                "total_steps": len(plan.steps),
                "completed_steps": len(completed_steps),
                "failed_steps": len(failed_steps),
                "success_rate": len(completed_steps) / len(plan.steps) if plan.steps else 0,
                "average_step_time": total_time / len(plan.steps) if plan.steps else 0
            }
        )
        
        # Сохраняем в историю
        self.execution_history.append(result)
        
        self.logger.info(f"✅ План выполнен: {len(completed_steps)}/{len(plan.steps)} шагов за {total_time:.2f}s")
        
        return result
    
    def _sort_steps_by_priority_and_dependencies(self, steps: List[Step]) -> List[Step]:
        """Сортировка шагов по приоритету и зависимостям"""
        # Простая топологическая сортировка с учетом приоритета
        sorted_steps = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            # Находим шаги без невыполненных зависимостей
            ready_steps = [
                step for step in remaining_steps
                if all(dep in [s.id for s in sorted_steps] for dep in step.dependencies)
            ]
            
            if not ready_steps:
                # Если нет готовых шагов, берем любой для избежания deadlock
                ready_steps = remaining_steps[:1]
            
            # Сортируем по приоритету
            ready_steps.sort(key=lambda s: s.priority.value, reverse=True)
            
            # Добавляем первый шаг
            step = ready_steps[0]
            sorted_steps.append(step)
            remaining_steps.remove(step)
        
        return sorted_steps
    
    def _check_dependencies(self, step: Step, completed_steps: List[Step]) -> bool:
        """Проверка выполнения зависимостей"""
        completed_ids = {s.id for s in completed_steps}
        return all(dep in completed_ids for dep in step.dependencies)
    
    def _combine_results(self, steps: List[Step]) -> Any:
        """Объединение результатов шагов"""
        results = []
        for step in steps:
            if step.result is not None:
                results.append({
                    "step_id": step.id,
                    "description": step.description,
                    "result": step.result,
                    "execution_time": step.execution_time
                })
        return results
    
    def _generate_error_summary(self, failed_steps: List[Step]) -> str:
        """Генерация сводки ошибок"""
        if not failed_steps:
            return ""
        
        errors = []
        for step in failed_steps:
            errors.append(f"Шаг {step.id}: {step.error}")
        
        return "; ".join(errors)
    
    async def plan_and_execute(self, task_description: str) -> ExecutionResult:
        """🎯 Основной метод - планирование и выполнение"""
        self.logger.info(f"🎯 Начинаю задачу: {task_description}")
        
        try:
            # Шаг 1: Анализ задачи
            analysis = await self.analyze_task(task_description)
            
            # Шаг 2: Создание плана
            plan = await self.create_plan(task_description, analysis)
            
            # Шаг 3: Валидация плана
            is_valid, issues = await self.validate_plan(plan)
            
            # Шаг 4: Улучшение плана если нужно
            if not is_valid:
                plan = await self.improve_plan(plan, issues)
                is_valid, issues = await self.validate_plan(plan)
                
                if not is_valid:
                    raise ValueError(f"Не удалось создать валидный план: {issues}")
            
            # Шаг 5: Выполнение плана
            result = await self.execute_plan(plan)
            
            self.logger.info(f"🎉 Задача завершена: {'успешно' if result.success else 'с ошибками'}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка выполнения задачи: {e}")
            raise e
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Получить статистику выполнения"""
        if not self.execution_history:
            return {}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for r in self.execution_history if r.success)
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions,
            "average_execution_time": sum(r.total_time for r in self.execution_history) / total_executions,
            "tool_usage": self.tool_registry.get_tool_stats()
        }
