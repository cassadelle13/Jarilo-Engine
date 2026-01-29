"""
🔌 Simple Plugin Manager - Упрощенная система плагинов

Только базовая загрузка и управление плагинами без избыточной сложности.
"""

import asyncio
import logging
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .plan_execute_agent import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

@dataclass
class SimplePluginInfo:
    """Простая информация о плагине"""
    id: str
    name: str
    version: str
    description: str
    tools: List[str]
    enabled: bool = True

class SimplePluginManager:
    """🔌 Упрощенный менеджер плагинов"""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(__name__)
        self.plugins_dir = Path("plugins")
        self.plugins_dir.mkdir(exist_ok=True)
        
        # Состояние
        self.installed_plugins: Dict[str, SimplePluginInfo] = {}
        
        # Загружаем установленные плагины
        asyncio.create_task(self._load_installed_plugins())
    
    async def _load_installed_plugins(self):
        """Загрузить установленные плагины"""
        self.logger.info("🔍 Загружаю плагины...")
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                try:
                    await self._load_plugin(plugin_dir)
                except Exception as e:
                    self.logger.error(f"❌ Ошибка загрузки плагина {plugin_dir.name}: {e}")
    
    async def _load_plugin(self, plugin_path: Path):
        """Загрузить плагин"""
        plugin_file = plugin_path / "plugin.py"
        
        if not plugin_file.exists():
            return
        
        try:
            # Динамически импортируем модуль
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_path.name}", plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Ищем классы инструментов
            tools = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseTool) and 
                    attr != BaseTool):
                    
                    # Создаем экземпляр инструмента
                    tool_instance = attr()
                    tools.append(tool_instance)
                    self.tool_registry.register_tool(tool_instance)
            
            # Сохраняем информацию о плагине
            plugin_info = SimplePluginInfo(
                id=plugin_path.name,
                name=getattr(module, 'PLUGIN_NAME', plugin_path.name),
                version=getattr(module, 'PLUGIN_VERSION', '1.0.0'),
                description=getattr(module, 'PLUGIN_DESCRIPTION', ''),
                tools=[tool.name for tool in tools],
                enabled=True
            )
            
            self.installed_plugins[plugin_path.name] = plugin_info
            
            self.logger.info(f"✅ Плагин {plugin_info.name} загружен ({len(tools)} инструментов)")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки плагина {plugin_path.name}: {e}")
    
    async def install_plugin(self, plugin_path: str) -> tuple[bool, str]:
        """Установить плагин из файла или директории"""
        try:
            source = Path(plugin_path)
            
            if not source.exists():
                return False, f"Файл не найден: {plugin_path}"
            
            if source.is_file() and source.suffix == '.py':
                # Копируем .py файл
                plugin_id = source.stem
                target_dir = self.plugins_dir / plugin_id
                target_dir.mkdir(exist_ok=True)
                target_file = target_dir / "plugin.py"
                
                import shutil
                shutil.copy2(source, target_file)
                
            elif source.is_dir():
                # Копируем директорию
                plugin_id = source.name
                target_dir = self.plugins_dir / plugin_id
                
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                
                import shutil
                shutil.copytree(source, target_dir)
            else:
                return False, "Неподдерживаемый формат плагина"
            
            # Загружаем плагин
            await self._load_plugin(target_dir)
            
            return True, f"Плагин {plugin_id} установлен успешно"
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка установки плагина: {e}")
            return False, f"Ошибка установки: {e}"
    
    async def uninstall_plugin(self, plugin_id: str) -> tuple[bool, str]:
        """Удалить плагин"""
        if plugin_id not in self.installed_plugins:
            return False, f"Плагин {plugin_id} не найден"
        
        try:
            plugin_info = self.installed_plugins[plugin_id]
            
            # Удаляем инструменты из реестра
            for tool_name in plugin_info.tools:
                if tool_name in self.tool_registry.tools:
                    del self.tool_registry.tools[tool_name]
            
            # Удаляем директорию плагина
            plugin_path = self.plugins_dir / plugin_id
            if plugin_path.exists():
                import shutil
                shutil.rmtree(plugin_path)
            
            # Удаляем из списка
            del self.installed_plugins[plugin_id]
            
            self.logger.info(f"✅ Плагин {plugin_id} удален")
            return True, f"Плагин {plugin_id} удален"
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка удаления плагина: {e}")
            return False, f"Ошибка удаления: {e}"
    
    def list_plugins(self) -> List[SimplePluginInfo]:
        """Получить список плагинов"""
        return list(self.installed_plugins.values())
    
    def get_plugin_info(self, plugin_id: str) -> Optional[SimplePluginInfo]:
        """Получить информацию о плагине"""
        return self.installed_plugins.get(plugin_id)
    
    async def enable_plugin(self, plugin_id: str) -> tuple[bool, str]:
        """Включить плагин"""
        if plugin_id not in self.installed_plugins:
            return False, f"Плагин {plugin_id} не найден"
        
        self.installed_plugins[plugin_id].enabled = True
        return True, f"Плагин {plugin_id} включен"
    
    async def disable_plugin(self, plugin_id: str) -> tuple[bool, str]:
        """Отключить плагин"""
        if plugin_id not in self.installed_plugins:
            return False, f"Плагин {plugin_id} не найден"
        
        plugin_info = self.installed_plugins[plugin_id]
        
        # Удаляем инструменты из реестра
        for tool_name in plugin_info.tools:
            if tool_name in self.tool_registry.tools:
                del self.tool_registry.tools[tool_name]
        
        plugin_info.enabled = False
        return True, f"Плагин {plugin_id} отключен"
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        total_plugins = len(self.installed_plugins)
        enabled_plugins = sum(1 for p in self.installed_plugins.values() if p.enabled)
        total_tools = sum(len(p.tools) for p in self.installed_plugins.values())
        
        return {
            "total_plugins": total_plugins,
            "enabled_plugins": enabled_plugins,
            "disabled_plugins": total_plugins - enabled_plugins,
            "total_tools": total_tools
        }

# 🎯 ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
_simple_plugin_manager = None

def get_simple_plugin_manager(tool_registry: ToolRegistry) -> SimplePluginManager:
    """Получить глобальный экземпляр менеджера плагинов"""
    global _simple_plugin_manager
    
    if _simple_plugin_manager is None:
        _simple_plugin_manager = SimplePluginManager(tool_registry)
    
    return _simple_plugin_manager
