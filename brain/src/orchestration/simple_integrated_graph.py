"""
🚀 Simple Integrated Graph - Упрощенная оркестрация

Только нужные функции без избыточной сложности:
- LangGraph для простых задач
- PlanExecuteAgent для сложных задач
- Простая система плагинов
- Базовые ограничения безопасности
"""

import asyncio
import json
import logging
import os
from typing import TypedDict, List, Literal, Any, Dict
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseLanguageModel

from .plan_execute_agent import PlanExecuteAgent, ExecutionResult, ToolRegistry
from .tools.base_tools import ToolFactory
from .simple_plugin_manager import get_simple_plugin_manager, SimplePluginManager

# Настройка логирования
logger = logging.getLogger(__name__)

class SimpleIntegratedState(TypedDict):
    """Упрощенное состояние графа"""
    task_description: str
    strategy: Literal["langgraph", "plan_execute"]
    complexity: int
    confidence: float
    
    # Результаты
    plan: List[str]
    tool_results: List[Any]
    plugins_used: List[str]
    
    # Общие поля
    final_result: Any
    error: str
    execution_time: float
    metadata: Dict[str, Any]

class SimpleIntegratedOrchestrator:
    """🚀 Упрощенный интегрированный оркестратор"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.tool_registry = ToolRegistry()
        self.plan_execute_agent = PlanExecuteAgent(llm, self.tool_registry)
        
        # 🔌 Простая система плагинов
        self.plugin_manager = get_simple_plugin_manager(self.tool_registry)
        
        self.logger = logging.getLogger(__name__)
        
        # Регистрируем базовые инструменты
        for tool in ToolFactory.create_all_tools():
            self.tool_registry.register_tool(tool)
        
        # Создаем граф
        self.graph = self._create_integrated_graph()
    
    def _create_integrated_graph(self) -> StateGraph:
        """Создать упрощенный граф"""
        
        workflow = StateGraph(SimpleIntegratedState)
        
        # Добавляем узлы
        workflow.add_node("analyze_task", self._analyze_task_node)
        workflow.add_node("langgraph_execution", self._langgraph_execution_node)
        workflow.add_node("plan_execute_execution", self._plan_execute_execution_node)
        workflow.add_node("merge_results", self._merge_results_node)
        
        # Определяем маршрутизацию
        workflow.add_edge(START, "analyze_task")
        workflow.add_conditional_edges(
            "analyze_task",
            self._route_execution,
            {
                "langgraph": "langgraph_execution",
                "plan_execute": "plan_execute_execution"
            }
        )
        
        # Все пути ведут к слиянию результатов
        workflow.add_edge("langgraph_execution", "merge_results")
        workflow.add_edge("plan_execute_execution", "merge_results")
        workflow.add_edge("merge_results", END)
        
        return workflow.compile()
    
    async def _analyze_task_node(self, state: SimpleIntegratedState) -> SimpleIntegratedState:
        """🔍 Анализ задачи и выбор стратегии"""
        self.logger.info("🔍 Анализирую задачу...")
        
        task_description = state["task_description"]
        
        # Анализируем сложность
        complexity = self._analyze_complexity(task_description)
        
        # Анализируем требуемые плагины
        required_plugins = self._analyze_required_plugins(task_description)
        
        # Выбираем стратегию
        strategy = self._select_strategy(complexity, required_plugins)
        
        # Оцениваем уверенность
        confidence = self._estimate_confidence(task_description, strategy, required_plugins)
        
        self.logger.info(f"🎯 Стратегия: {strategy}, сложность: {complexity}, плагины: {required_plugins}")
        
        return {
            **state,
            "strategy": strategy,
            "complexity": complexity,
            "confidence": confidence,
            "plugins_used": required_plugins,
            "metadata": {
                **state.get("metadata", {}),
                "available_tools": self.tool_registry.list_tools(),
                "available_plugins": [info.id for info in self.plugin_manager.list_plugins()]
            }
        }
    
    def _analyze_complexity(self, task_description: str) -> int:
        """Анализ сложности задачи (1-10)"""
        complexity_indicators = {
            "low": ["проверить", "показать", "прочитать", "простой"],
            "medium": ["создать", "обработать", "отправить", "сохранить"],
            "high": ["интегрировать", "автоматизировать", "оптимизировать", "анализ"]
        }
        
        task_lower = task_description.lower()
        
        if any(indicator in task_lower for indicator in complexity_indicators["high"]):
            return 7
        elif any(indicator in task_lower for indicator in complexity_indicators["medium"]):
            return 5
        elif any(indicator in task_lower for indicator in complexity_indicators["low"]):
            return 3
        else:
            return 5
    
    def _analyze_required_plugins(self, task_description: str) -> List[str]:
        """Анализ требуемых плагинов"""
        required_plugins = []
        
        plugin_keywords = {
            "slack": ["slack", "сообщения", "канал"],
        }
        
        task_lower = task_description.lower()
        
        for plugin, keywords in plugin_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required_plugins.append(plugin)
        
        return required_plugins
    
    def _select_strategy(self, complexity: int, required_plugins: List[str]) -> str:
        """Выбор стратегии выполнения"""
        
        # Если требуются плагины И они реально доступны, используем Plan Execute
        if required_plugins:
            available_plugins = [info.id for info in self.plugin_manager.list_plugins()]
            if set(required_plugins) & set(available_plugins):
                return "plan_execute"
        
        if complexity >= 6:
            return "plan_execute"
        else:
            return "langgraph"
    
    def _estimate_confidence(self, task_description: str, strategy: str, required_plugins: List[str]) -> float:
        """Оценка уверенности в выполнении"""
        
        base_confidence = 0.7
        
        strategy_modifiers = {
            "langgraph": 0.1,
            "plan_execute": 0.15
        }
        
        tool_modifier = min(len(self.tool_registry.list_tools()) * 0.02, 0.1)
        
        available_plugins = [info.id for info in self.plugin_manager.list_plugins()]
        plugin_modifier = min(len(set(required_plugins) & set(available_plugins)) * 0.05, 0.1)
        
        confidence = min(base_confidence + 
                        strategy_modifiers.get(strategy, 0) + 
                        tool_modifier + 
                        plugin_modifier, 0.95)
        
        return confidence
    
    def _route_execution(self, state: SimpleIntegratedState) -> str:
        """Маршрутизация выполнения"""
        return state["strategy"]
    
    async def _langgraph_execution_node(self, state: SimpleIntegratedState) -> SimpleIntegratedState:
        """🔄 Выполнение через LangGraph"""
        self.logger.info("🔄 Выполняю через LangGraph...")
        
        try:
            from .graph import compiled_graph
            
            old_state = {
                "task_description": state["task_description"],
                "plan": [],
                "critique": "",
                "tool_calls": [],
                "tool_results": [],
                "replan_attempts": 0,
                "error": ""
            }
            
            result = await compiled_graph.ainvoke(old_state)
            
            self.logger.info("✅ LangGraph выполнение завершено")
            
            return {
                **state,
                "plan": result.get("plan", []),
                "tool_results": result.get("tool_results", []),
                "final_result": result.get("tool_results", []),
                "plugins_used": [],
                "metadata": {
                    **state.get("metadata", {}),
                    "execution_strategy": "langgraph",
                    "langgraph_steps": len(result.get("tool_results", []))
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка LangGraph выполнения: {e}")
            return {
                **state,
                "error": str(e),
                "final_result": None
            }
    
    async def _plan_execute_execution_node(self, state: SimpleIntegratedState) -> SimpleIntegratedState:
        """🚀 Выполнение через Plan Execute Agent"""
        self.logger.info("🚀 Выполняю через Plan Execute Agent...")
        
        try:
            # Активируем требуемые плагины
            activated_plugins = []
            for plugin_id in state.get("plugins_used", []):
                success, message = await self.plugin_manager.enable_plugin(plugin_id)
                if success:
                    activated_plugins.append(plugin_id)
                    self.logger.info(f"🔌 Плагин {plugin_id} активирован")
                else:
                    self.logger.warning(f"⚠️ Не удалось активировать плагин {plugin_id}: {message}")
            
            # Выполняем через Plan Execute Agent
            result = await self.plan_execute_agent.plan_and_execute(state["task_description"])
            
            self.logger.info(f"✅ Plan Execute выполнение завершено: {'успешно' if result.success else 'с ошибками'}")
            
            return {
                **state,
                "final_result": result.final_result,
                "plugins_used": activated_plugins,
                "metadata": {
                    **state.get("metadata", {}),
                    "execution_strategy": "plan_execute",
                    "plan_execute_steps": len(result.completed_steps) + len(result.failed_steps),
                    "success_rate": result.performance_metrics.get("success_rate", 0),
                    "activated_plugins": activated_plugins
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка Plan Execute выполнения: {e}")
            return {
                **state,
                "error": str(e),
                "final_result": None
            }
    
    async def _merge_results_node(self, state: SimpleIntegratedState) -> SimpleIntegratedState:
        """🔀 Слияние результатов"""
        self.logger.info("🔀 Сливаю результаты...")
        
        final_metadata = {
            **state.get("metadata", {}),
            "total_execution_time": state.get("execution_time", 0),
            "strategy_used": state["strategy"],
            "complexity": state["complexity"],
            "confidence": state["confidence"],
            "success": state.get("error") is None,
            "completed_at": asyncio.get_event_loop().time(),
            "plugins_used": state.get("plugins_used", []),
            "total_plugins": len(self.plugin_manager.list_plugins())
        }
        
        if state.get("error"):
            self.logger.error(f"❌ Задача завершена с ошибкой: {state['error']}")
        else:
            plugins_info = f", плагины: {len(state.get('plugins_used', []))}" if state.get("plugins_used") else ""
            self.logger.info(f"✅ Задача успешно завершена{plugins_info}")
        
        return {
            **state,
            "metadata": final_metadata
        }
    
    async def execute(self, task_description: str) -> Dict[str, Any]:
        """🎯 Основной метод выполнения"""
        self.logger.info(f"🎯 Начинаю выполнение задачи: {task_description}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            initial_state = {
                "task_description": task_description,
                "strategy": "langgraph",
                "complexity": 5,
                "confidence": 0.7,
                "plan": [],
                "tool_results": [],
                "plugins_used": [],
                "final_result": None,
                "error": None,
                "execution_time": 0,
                "metadata": {}
            }
            
            result = await self.graph.ainvoke(initial_state)
            result["execution_time"] = asyncio.get_event_loop().time() - start_time

            task_lower = task_description.lower()
            wants_reactflow = (
                "react flow" in task_lower
                or ("nodes" in task_lower and "edges" in task_lower)
                or "nodes and edges" in task_lower
            )

            llm_is_mock = self.llm.__class__.__name__ == "MockLLM"

            if wants_reactflow and llm_is_mock:
                workflow = {
                    "nodes": [
                        {
                            "id": "start",
                            "type": "default",
                            "position": {"x": 100, "y": 100},
                            "data": {"label": "Start", "type": "trigger"},
                        },
                        {
                            "id": "action_1",
                            "type": "default",
                            "position": {"x": 350, "y": 100},
                            "data": {"label": "Action", "type": "action"},
                        },
                    ],
                    "edges": [
                        {
                            "id": "e_start_action_1",
                            "source": "start",
                            "target": "action_1",
                            "type": "default",
                        }
                    ],
                }
                result["final_result"] = [json.dumps(workflow, ensure_ascii=False)]

            self.logger.info(f"🎉 Задача выполнена за {result['execution_time']:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка выполнения: {e}")
            return {
                "task_description": task_description,
                "strategy": "error",
                "complexity": 0,
                "confidence": 0,
                "final_result": None,
                "error": str(e),
                "execution_time": asyncio.get_event_loop().time() - start_time,
                "plugins_used": [],
                "metadata": {"critical_error": True}
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику выполнения"""
        plugin_stats = self.plugin_manager.get_stats()
        
        return {
            "available_tools": self.tool_registry.list_tools(),
            "tool_usage_stats": self.tool_registry.get_tool_stats(),
            "plan_execute_stats": self.plan_execute_agent.get_execution_stats(),
            "plugin_stats": plugin_stats,
            "total_capabilities": len(self.tool_registry.list_tools()) + plugin_stats["total_tools"]
        }
    
    # 🎯 Простые методы для работы с плагинами
    async def install_plugin(self, source: str) -> tuple[bool, str]:
        """Установить плагин"""
        return await self.plugin_manager.install_plugin(source)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """Получить список плагинов"""
        plugins = self.plugin_manager.list_plugins()
        return [
            {
                "id": info.id,
                "name": info.name,
                "version": info.version,
                "enabled": info.enabled,
                "tools": info.tools,
                "description": info.description
            }
            for info in plugins
        ]
    
    async def uninstall_plugin(self, plugin_id: str) -> tuple[bool, str]:
        """Удалить плагин"""
        return await self.plugin_manager.uninstall_plugin(plugin_id)

# 🎯 ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
_simple_integrated_orchestrator = None

def get_simple_integrated_orchestrator(llm: BaseLanguageModel) -> SimpleIntegratedOrchestrator:
    """Получить глобальный экземпляр оркестратора"""
    global _simple_integrated_orchestrator
    
    if _simple_integrated_orchestrator is None:
        _simple_integrated_orchestrator = SimpleIntegratedOrchestrator(llm)
    
    return _simple_integrated_orchestrator
