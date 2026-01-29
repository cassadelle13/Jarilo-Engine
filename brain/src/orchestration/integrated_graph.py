"""
🚀 Integrated Graph - объединение LangGraph и Plan Execute Agent

Новая архитектура:
- LangGraph для базовой оркестрации
- PlanExecuteAgent для сложных задач
- Plugin System для расширяемости
- Sandbox Execution для безопасности
- Интеллектуальный выбор стратегии выполнения
"""

import asyncio
import logging
from typing import TypedDict, List, Literal, Any, Dict
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseLanguageModel

from .plan_execute_agent import PlanExecuteAgent, ExecutionResult, ExecutionPlan
from .tools.base_tools import ToolFactory
from .plugin_manager import get_plugin_manager, PluginManager
from .sandbox import get_sandbox_manager, SandboxManager, SandboxConfig, SandboxType, SecurityLevel

# Настройка логирования
logger = logging.getLogger(__name__)

class IntegratedState(TypedDict):
    """Интегрированное состояние графа"""
    task_description: str
    strategy: Literal["langgraph", "plan_execute", "hybrid"]
    complexity: int
    confidence: float
    
    # LangGraph результаты
    plan: List[str]
    critique: str
    tool_calls: List[Any]
    tool_results: List[Any]
    
    # Plan Execute результаты
    execution_plan: ExecutionPlan
    execution_result: ExecutionResult
    
    # Plugin System результаты
    plugins_used: List[str]
    sandbox_used: bool
    
    # Общие поля
    final_result: Any
    error: str
    execution_time: float
    metadata: Dict[str, Any]

class IntegratedOrchestrator:
    """🚀 Интегрированный оркестратор с Plugin System"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.tool_registry = ToolRegistry()
        self.plan_execute_agent = PlanExecuteAgent(llm, self.tool_registry)
        
        # 🎯 Plugin System
        self.plugin_manager = get_plugin_manager(self.tool_registry)
        
        # 🔒 Sandbox System
        self.sandbox_manager = get_sandbox_manager()
        
        self.logger = logging.getLogger(__name__)
        
        # Регистрируем базовые инструменты
        for tool in ToolFactory.create_all_tools():
            self.tool_registry.register_tool(tool)
        
        # 🎯 Регистрируем sandbox инструменты
        from .sandbox import SandboxedToolFactory
        sandbox_config = SandboxConfig(
            sandbox_type=SandboxType.PROCESS,
            security_level=SecurityLevel.STANDARD,
            timeout=30,
            memory_limit="256m"
        )
        
        for tool in SandboxedToolFactory.create_all_tools(sandbox_config):
            self.tool_registry.register_tool(tool)
        
        # Создаем граф
        self.graph = self._create_integrated_graph()
    
    def _create_integrated_graph(self) -> StateGraph:
        """Создать интегрированный граф"""
        
        # Создаем граф
        workflow = StateGraph(IntegratedState)
        
        # Добавляем узлы
        workflow.add_node("analyze_task", self._analyze_task_node)
        workflow.add_node("langgraph_execution", self._langgraph_execution_node)
        workflow.add_node("plan_execute_execution", self._plan_execute_execution_node)
        workflow.add_node("hybrid_execution", self._hybrid_execution_node)
        workflow.add_node("merge_results", self._merge_results_node)
        
        # Определяем маршрутизацию
        workflow.add_edge(START, "analyze_task")
        workflow.add_conditional_edges(
            "analyze_task",
            self._route_execution,
            {
                "langgraph": "langgraph_execution",
                "plan_execute": "plan_execute_execution",
                "hybrid": "hybrid_execution"
            }
        )
        
        # Все пути ведут к слиянию результатов
        workflow.add_edge("langgraph_execution", "merge_results")
        workflow.add_edge("plan_execute_execution", "merge_results")
        workflow.add_edge("hybrid_execution", "merge_results")
        workflow.add_edge("merge_results", END)
        
        return workflow.compile()
    
    async def _analyze_task_node(self, state: IntegratedState) -> IntegratedState:
        """🔍 Анализ задачи и выбор стратегии с поддержкой плагинов"""
        self.logger.info("🔍 Анализирую задачу и выбираю стратегию...")
        
        task_description = state["task_description"]
        
        # Анализируем сложность задачи
        complexity = await self._analyze_complexity(task_description)
        
        # 🎯 Анализируем требуемые плагины
        required_plugins = await self._analyze_required_plugins(task_description)
        
        # Выбираем стратегию
        strategy = self._select_strategy(complexity, task_description, required_plugins)
        
        # Оцениваем уверенность
        confidence = await self._estimate_confidence(task_description, strategy, required_plugins)
        
        # 🔒 Определяем необходимость песочницы
        needs_sandbox = await self._needs_sandbox(task_description, complexity)
        
        self.logger.info(f"🎯 Стратегия выбрана: {strategy}, сложность: {complexity}, уверенность: {confidence}")
        self.logger.info(f"🔌 Требуемые плагины: {required_plugins}, песочница: {needs_sandbox}")
        
        return {
            **state,
            "strategy": strategy,
            "complexity": complexity,
            "confidence": confidence,
            "plugins_used": required_plugins,
            "sandbox_used": needs_sandbox,
            "metadata": {
                **state.get("metadata", {}),
                "analysis_time": asyncio.get_event_loop().time(),
                "available_tools": self.tool_registry.list_tools(),
                "available_plugins": [info.metadata.id for info in self.plugin_manager.list_plugins()],
                "sandbox_available": self.sandbox_manager.get_available_sandboxes()
            }
        }
    
    async def _analyze_required_plugins(self, task_description: str) -> List[str]:
        """🔌 Анализ требуемых плагинов"""
        required_plugins = []
        
        # Простая эвристика на основе ключевых слов
        plugin_keywords = {
            "slack": ["slack", "сообщения", "канал"],
            "email": ["email", "письмо", "отправить"],
            "database": ["база данных", "sql", "бд"],
            "api": ["api", "http", "запрос"],
            "file": ["файл", "диск", "папка"]
        }
        
        task_lower = task_description.lower()
        
        for plugin, keywords in plugin_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required_plugins.append(plugin)
        
        return required_plugins
    
    async def _needs_sandbox(self, task_description: str, complexity: int) -> bool:
        """🔒 Определить необходимость песочницы"""
        # Высокая сложность или подозрительные операции требуют песочницу
        sandbox_indicators = [
            "выполнить код", "python", "javascript", "shell",
            "системная команда", "процесс", "запустить"
        ]
        
        task_lower = task_description.lower()
        
        if complexity >= 8:
            return True
        
        return any(indicator in task_lower for indicator in sandbox_indicators)
    
    def _select_strategy(self, complexity: int, task_description: str, required_plugins: List[str]) -> str:
        """Выбор стратегии выполнения с учетом плагинов"""
        
        # Если требуются плагины, используем Plan Execute
        if required_plugins:
            return "plan_execute"
        
        if complexity >= 8:
            return "plan_execute"  # Сложные задачи - Plan Execute
        elif complexity <= 4:
            return "langgraph"    # Простые задачи - LangGraph
        else:
            return "hybrid"        # Средние задачи - гибрид
    
    async def _estimate_confidence(self, task_description: str, strategy: str, required_plugins: List[str]) -> float:
        """Оценка уверенности в выполнении"""
        
        # Базовая уверенность
        base_confidence = 0.7
        
        # Модификаторы в зависимости от стратегии
        strategy_modifiers = {
            "langgraph": 0.1,
            "plan_execute": 0.15,
            "hybrid": 0.05
        }
        
        # Модификаторы в зависимости от доступных инструментов
        tool_modifier = min(len(self.tool_registry.list_tools()) * 0.02, 0.1)
        
        # Модификаторы в зависимости от доступных плагинов
        available_plugins = [info.metadata.id for info in self.plugin_manager.list_plugins()]
        plugin_modifier = min(len(set(required_plugins) & set(available_plugins)) * 0.05, 0.15)
        
        confidence = min(base_confidence + 
                        strategy_modifiers.get(strategy, 0) + 
                        tool_modifier + 
                        plugin_modifier, 0.95)
        
        return confidence
    
    def _route_execution(self, state: IntegratedState) -> str:
        """Маршрутизация выполнения"""
        return state["strategy"]
    
    async def _langgraph_execution_node(self, state: IntegratedState) -> IntegratedState:
        """🔄 Выполнение через LangGraph"""
        self.logger.info("🔄 Выполняю через LangGraph...")
        
        try:
            # Импортируем старый граф
            from .graph import compiled_graph
            
            # Создаем состояние для старого графа
            old_state = {
                "task_description": state["task_description"],
                "plan": [],
                "critique": "",
                "tool_calls": [],
                "tool_results": [],
                "replan_attempts": 0,
                "error": ""
            }
            
            # Выполняем старый граф
            result = await compiled_graph.ainvoke(old_state)
            
            self.logger.info("✅ LangGraph выполнение завершено")
            
            return {
                **state,
                "plan": result.get("plan", []),
                "tool_results": result.get("tool_results", []),
                "final_result": result.get("tool_results", []),
                "metadata": {
                    **state.get("metadata", {}),
                    "execution_strategy": "langgraph",
                    "langgraph_steps": len(result.get("tool_results", [])),
                    "plugins_used": [],
                    "sandbox_used": False
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка LangGraph выполнения: {e}")
            return {
                **state,
                "error": str(e),
                "final_result": None
            }
    
    async def _plan_execute_execution_node(self, state: IntegratedState) -> IntegratedState:
        """🚀 Выполнение через Plan Execute Agent с поддержкой плагинов"""
        self.logger.info("🚀 Выполняю через Plan Execute Agent...")
        
        try:
            # 🔌 Активируем требуемые плагины
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
                "execution_result": result,
                "final_result": result.final_result,
                "plugins_used": activated_plugins,
                "metadata": {
                    **state.get("metadata", {}),
                    "execution_strategy": "plan_execute",
                    "plan_execute_steps": len(result.completed_steps) + len(result.failed_steps),
                    "success_rate": result.performance_metrics.get("success_rate", 0),
                    "activated_plugins": activated_plugins,
                    "sandbox_used": state.get("sandbox_used", False)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка Plan Execute выполнения: {e}")
            return {
                **state,
                "error": str(e),
                "final_result": None
            }
    
    async def _hybrid_execution_node(self, state: IntegratedState) -> IntegratedState:
        """🎯 Гибридное выполнение с поддержкой плагинов"""
        self.logger.info("🎯 Выполняю гибридную стратегию...")
        
        try:
            # Сначала пробуем LangGraph для быстрого результата
            langgraph_result = await self._langgraph_execution_node(state)
            
            # Если LangGraph не справился, используем Plan Execute с плагинами
            if langgraph_result.get("error") or not langgraph_result.get("final_result"):
                self.logger.info("🔄 LangGraph не справился, переключаюсь на Plan Execute с плагинами...")
                plan_execute_result = await self._plan_execute_execution_node(state)
                
                return {
                    **state,
                    "execution_result": plan_execute_result.get("execution_result"),
                    "final_result": plan_execute_result.get("final_result"),
                    "plugins_used": plan_execute_result.get("plugins_used", []),
                    "metadata": {
                        **state.get("metadata", {}),
                        "execution_strategy": "hybrid_fallback",
                        "langgraph_failed": True,
                        "plan_execute_used": True,
                        "plugins_used": plan_execute_result.get("plugins_used", []),
                        "sandbox_used": state.get("sandbox_used", False)
                    }
                }
            else:
                # LangGraph справился
                self.logger.info("✅ LangGraph справился, используем его результат")
                return langgraph_result
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка гибридного выполнения: {e}")
            return {
                **state,
                "error": str(e),
                "final_result": None
            }
    
    async def _merge_results_node(self, state: IntegratedState) -> IntegratedState:
        """🔀 Слияние результатов с информацией о плагинах и песочнице"""
        self.logger.info("🔀 Сливаю результаты...")
        
        # Добавляем финальные метаданные
        final_metadata = {
            **state.get("metadata", {}),
            "total_execution_time": state.get("execution_time", 0),
            "strategy_used": state["strategy"],
            "complexity": state["complexity"],
            "confidence": state["confidence"],
            "success": state.get("error") is None,
            "completed_at": asyncio.get_event_loop().time(),
            "plugins_used": state.get("plugins_used", []),
            "sandbox_used": state.get("sandbox_used", False),
            "total_plugins": len(self.plugin_manager.list_plugins()),
            "active_plugins": len([p for p in self.plugin_manager.list_plugins() if p.status.value == "active"]),
            "available_sandboxes": self.sandbox_manager.get_available_sandboxes()
        }
        
        # Логируем итоговый результат
        if state.get("error"):
            self.logger.error(f"❌ Задача завершена с ошибкой: {state['error']}")
        else:
            plugins_info = f", плагины: {len(state.get('plugins_used', []))}" if state.get("plugins_used") else ""
            sandbox_info = ", песочница: да" if state.get("sandbox_used") else ""
            self.logger.info(f"✅ Задача успешно завершена{plugins_info}{sandbox_info}")
        
        return {
            **state,
            "metadata": final_metadata
        }
    
    async def execute(self, task_description: str) -> Dict[str, Any]:
        """🎯 Основной метод выполнения с поддержкой Plugin System"""
        self.logger.info(f"🎯 Начинаю выполнение задачи: {task_description}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Начальное состояние
            initial_state = {
                "task_description": task_description,
                "strategy": "langgraph",
                "complexity": 5,
                "confidence": 0.7,
                "plan": [],
                "critique": "",
                "tool_calls": [],
                "tool_results": [],
                "execution_plan": None,
                "execution_result": None,
                "final_result": None,
                "error": "",
                "execution_time": 0,
                "plugins_used": [],
                "sandbox_used": False,
                "metadata": {}
            }
            
            # Выполняем граф
            result = await self.graph.ainvoke(initial_state)
            
            # Добавляем время выполнения
            result["execution_time"] = asyncio.get_event_loop().time() - start_time
            
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
                "sandbox_used": False,
                "metadata": {"critical_error": True}
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику выполнения"""
        plugin_stats = self.plugin_manager.get_stats()
        sandbox_stats = self.sandbox_manager.get_available_sandboxes()
        
        return {
            "available_tools": self.tool_registry.list_tools(),
            "tool_usage_stats": self.tool_registry.get_tool_stats(),
            "plan_execute_stats": self.plan_execute_agent.get_execution_stats(),
            "plugin_stats": plugin_stats,
            "sandbox_stats": sandbox_stats,
            "total_capabilities": len(self.tool_registry.list_tools()) + plugin_stats["total_tools"]
        }
    
    # 🎯 НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ПЛАГИНАМИ
    async def install_plugin(self, source: str) -> tuple[bool, str]:
        """Установить плагин"""
        return await self.plugin_manager.install_plugin(source)
    
    async def search_plugins(self, query: str) -> List[Dict[str, Any]]:
        """Поиск плагинов"""
        from .marketplace import get_marketplace_manager, SearchFilters
        
        marketplace = get_marketplace_manager(self.plugin_manager)
        plugins, _ = await marketplace.search_and_install(query)
        
        return [asdict(plugin.metadata) for plugin in plugins]
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """Получить список плагинов"""
        plugins = self.plugin_manager.list_plugins()
        return [
            {
                "id": info.metadata.id,
                "name": info.metadata.name,
                "version": info.metadata.version,
                "status": info.status.value,
                "tools": info.tools,
                "description": info.metadata.description
            }
            for info in plugins
        ]
    
    async def enable_plugin(self, plugin_id: str) -> tuple[bool, str]:
        """Включить плагин"""
        return await self.plugin_manager.enable_plugin(plugin_id)
    
    async def disable_plugin(self, plugin_id: str) -> tuple[bool, str]:
        """Отключить плагин"""
        return await self.plugin_manager.disable_plugin(plugin_id)
    
    async def uninstall_plugin(self, plugin_id: str) -> tuple[bool, str]:
        """Удалить плагин"""
        return await self.plugin_manager.uninstall_plugin(plugin_id)

# 🎯 ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
_integrated_orchestrator = None

def get_integrated_orchestrator(llm: BaseLanguageModel) -> IntegratedOrchestrator:
    """Получить глобальный экземпляр оркестратора"""
    global _integrated_orchestrator
    
    if _integrated_orchestrator is None:
        _integrated_orchestrator = IntegratedOrchestrator(llm)
    
    return _integrated_orchestrator

# 🚀 СКОМПИЛИРОВАННЫЙ ГРАФ (для обратной совместимости)
async def get_compiled_graph():
    """Получить скомпилированный граф (обратная совместимость)"""
    from .graph import get_llm
    
    llm = await get_llm()
    orchestrator = get_integrated_orchestrator(llm)
    
    return orchestrator.graph
