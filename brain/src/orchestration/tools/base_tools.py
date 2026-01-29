"""
🛠️ Базовые инструменты для Plan Execute Agent

Написано с нуля по лучшим практикам, но без копирования кода
"""

import asyncio
import json
import logging
import os
import subprocess
import aiofiles
import aiohttp
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..plan_execute_agent import BaseTool

logger = logging.getLogger(__name__)

class FileTool(BaseTool):
    """📁 Инструмент для работы с файлами"""
    
    def __init__(self):
        super().__init__("file_tool", "Работа с файлами: чтение, запись, создание, удаление")
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Выполнить файловую операцию"""
        operation = parameters.get("operation")
        file_path = parameters.get("path")
        content = parameters.get("content", "")
        
        if not file_path:
            raise ValueError("Путь к файлу обязателен")
        
        path = Path(file_path)
        
        if operation == "read":
            return await self._read_file(path)
        elif operation == "write":
            return await self._write_file(path, content)
        elif operation == "append":
            return await self._append_file(path, content)
        elif operation == "delete":
            return await self._delete_file(path)
        elif operation == "exists":
            return await self._file_exists(path)
        elif operation == "list":
            return await self._list_directory(path)
        else:
            raise ValueError(f"Неподдерживаемая операция: {operation}")
    
    async def _read_file(self, path: Path) -> str:
        """Прочитать файл"""
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            logger.info(f"📁 Файл прочитан: {path}")
            return content
        except Exception as e:
            logger.error(f"❌ Ошибка чтения файла {path}: {e}")
            raise e
    
    async def _write_file(self, path: Path, content: str) -> str:
        """Записать файл"""
        try:
            # Создаем директорию если нужна
            path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"📁 Файл записан: {path}")
            return f"Файл успешно записан: {path}"
        except Exception as e:
            logger.error(f"❌ Ошибка записи файла {path}: {e}")
            raise e
    
    async def _append_file(self, path: Path, content: str) -> str:
        """Добавить в файл"""
        try:
            async with aiofiles.open(path, 'a', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"📁 Контент добавлен в файл: {path}")
            return f"Контент добавлен в файл: {path}"
        except Exception as e:
            logger.error(f"❌ Ошибка добавления в файл {path}: {e}")
            raise e
    
    async def _delete_file(self, path: Path) -> str:
        """Удалить файл"""
        try:
            if path.exists():
                path.unlink()
                logger.info(f"📁 Файл удален: {path}")
                return f"Файл удален: {path}"
            else:
                return f"Файл не существует: {path}"
        except Exception as e:
            logger.error(f"❌ Ошибка удаления файла {path}: {e}")
            raise e
    
    async def _file_exists(self, path: Path) -> bool:
        """Проверить существование файла"""
        return path.exists()
    
    async def _list_directory(self, path: Path) -> List[str]:
        """Показать содержимое директории"""
        try:
            if not path.exists():
                return []
            
            if path.is_file():
                return [str(path)]
            
            items = []
            for item in path.iterdir():
                items.append(str(item))
            
            logger.info(f"📁 Директория прочитана: {path}, элементов: {len(items)}")
            return items
        except Exception as e:
            logger.error(f"❌ Ошибка чтения директории {path}: {e}")
            raise e
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Валидировать параметры"""
        required_fields = ["operation", "path"]
        return all(field in parameters for field in required_fields)
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Получить схему параметров"""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "append", "delete", "exists", "list"],
                    "description": "Тип операции"
                },
                "path": {
                    "type": "string",
                    "description": "Путь к файлу или директории"
                },
                "content": {
                    "type": "string",
                    "description": "Содержимое для записи/добавления"
                }
            },
            "required": ["operation", "path"]
        }

class PythonTool(BaseTool):
    """🐍 Инструмент для выполнения Python кода"""
    
    def __init__(self):
        super().__init__("python_tool", "Выполнение Python кода")
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Выполнить Python код"""
        code = parameters.get("code")
        timeout = parameters.get("timeout", 30)
        
        if not code:
            raise ValueError("Python код обязателен")
        
        try:
            # Создаем временный файл
            temp_file = Path("temp_execution.py")
            async with aiofiles.open(temp_file, 'w', encoding='utf-8') as f:
                await f.write(code)
            
            # Выполняем код
            process = await asyncio.create_subprocess_exec(
                "python", str(temp_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Выполнение кода превысило {timeout} секунд")
            
            # Удаляем временный файл
            temp_file.unlink(missing_ok=True)
            
            result = {
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "returncode": process.returncode
            }
            
            if process.returncode == 0:
                logger.info("🐍 Python код выполнен успешно")
                return result
            else:
                logger.warning(f"⚠️ Python код завершился с кодом {process.returncode}")
                raise RuntimeError(f"Python execution failed: {result['stderr']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения Python кода: {e}")
            raise e
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Валидировать параметры"""
        return "code" in parameters
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Получить схему параметров"""
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python код для выполнения"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Таймаут выполнения в секундах",
                    "default": 30
                }
            },
            "required": ["code"]
        }

class APITool(BaseTool):
    """🌐 Инструмент для HTTP запросов"""
    
    def __init__(self):
        super().__init__("api_tool", "Выполнение HTTP запросов к API")
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Выполнить HTTP запрос"""
        url = parameters.get("url")
        method = parameters.get("method", "GET").upper()
        headers = parameters.get("headers", {})
        data = parameters.get("data")
        params = parameters.get("params")
        timeout = parameters.get("timeout", 30)
        
        if not url:
            raise ValueError("URL обязателен")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                # Выполняем запрос
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data and method in ["POST", "PUT", "PATCH"] else None,
                    params=params
                ) as response:
                    
                    result = {
                        "status": response.status,
                        "status_text": response.reason,
                        "headers": dict(response.headers),
                        "url": str(response.url)
                    }
                    
                    # Читаем тело ответа
                    content_type = response.headers.get('content-type', '')
                    
                    if 'application/json' in content_type:
                        result["data"] = await response.json()
                    else:
                        result["data"] = await response.text()
                    
                    logger.info(f"🌐 {method} запрос к {url} завершен со статусом {response.status}")
                    
                    if response.status >= 400:
                        raise RuntimeError(f"HTTP {response.status}: {result['data']}")
                    
                    return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка HTTP запроса: {e}")
            raise e
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Валидировать параметры"""
        return "url" in parameters
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Получить схему параметров"""
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL для запроса"
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "default": "GET",
                    "description": "HTTP метод"
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP заголовки"
                },
                "data": {
                    "description": "Тело запроса"
                },
                "params": {
                    "type": "object",
                    "description": "URL параметры"
                },
                "timeout": {
                    "type": "integer",
                    "default": 30,
                    "description": "Таймаут в секундах"
                }
            },
            "required": ["url"]
        }

class DatabaseTool(BaseTool):
    """🗄️ Инструмент для работы с базами данных"""
    
    def __init__(self):
        super().__init__("database_tool", "Выполнение SQL запросов к базам данных")
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Выполнить SQL запрос"""
        query = parameters.get("query")
        db_type = parameters.get("db_type", "sqlite")
        connection_string = parameters.get("connection_string", ":memory:")
        
        if not query:
            raise ValueError("SQL запрос обязателен")
        
        try:
            if db_type.lower() == "sqlite":
                return await self._execute_sqlite(query, connection_string)
            else:
                raise ValueError(f"Неподдерживаемый тип БД: {db_type}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения SQL запроса: {e}")
            raise e
    
    async def _execute_sqlite(self, query: str, connection_string: str) -> Any:
        """Выполнить SQLite запрос"""
        import aiosqlite
        
        async with aiosqlite.connect(connection_string) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(query)
            
            # Определяем тип запроса
            query_lower = query.lower().strip()
            
            if query_lower.startswith("select"):
                rows = await cursor.fetchall()
                result = [dict(row) for row in rows]
                logger.info(f"🗄️ SELECT запрос вернул {len(result)} строк")
                return result
            else:
                await db.commit()
                affected_rows = cursor.rowcount
                logger.info(f"🗄️ Запрос выполнен, затронуто строк: {affected_rows}")
                return {"affected_rows": affected_rows}
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Валидировать параметры"""
        return "query" in parameters
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Получить схему параметров"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL запрос"
                },
                "db_type": {
                    "type": "string",
                    "enum": ["sqlite"],
                    "default": "sqlite",
                    "description": "Тип базы данных"
                },
                "connection_string": {
                    "type": "string",
                    "default": ":memory:",
                    "description": "Строка подключения"
                }
            },
            "required": ["query"]
        }

class EmailTool(BaseTool):
    """📧 Инструмент для отправки email"""
    
    def __init__(self):
        super().__init__("email_tool", "Отправка email сообщений")
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Отправить email"""
        to = parameters.get("to")
        subject = parameters.get("subject")
        body = parameters.get("body")
        smtp_server = parameters.get("smtp_server", "localhost")
        smtp_port = parameters.get("smtp_port", 587)
        username = parameters.get("username")
        password = parameters.get("password")
        
        if not all([to, subject, body]):
            raise ValueError("Поля to, subject, body обязательны")
        
        try:
            import aiosmtplib
            
            message = f"Subject: {subject}\n\n{body}"
            
            await aiosmtplib.send(
                message,
                hostname=smtp_server,
                port=smtp_port,
                username=username,
                password=password,
                timeout=30
            )
            
            logger.info(f"📧 Email отправлен на {to}")
            return f"Email успешно отправлен на {to}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки email: {e}")
            raise e
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Валидировать параметры"""
        required = ["to", "subject", "body"]
        return all(field in parameters for field in required)
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Получить схему параметров"""
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Email получателя"
                },
                "subject": {
                    "type": "string",
                    "description": "Тема письма"
                },
                "body": {
                    "type": "string",
                    "description": "Тело письма"
                },
                "smtp_server": {
                    "type": "string",
                    "default": "localhost",
                    "description": "SMTP сервер"
                },
                "smtp_port": {
                    "type": "integer",
                    "default": 587,
                    "description": "SMTP порт"
                },
                "username": {
                    "type": "string",
                    "description": "Имя пользователя"
                },
                "password": {
                    "type": "string",
                    "description": "Пароль"
                }
            },
            "required": ["to", "subject", "body"]
        }

# 🎯 ФАБРИКА ИНСТРУМЕНТОВ
class ToolFactory:
    """Фабрика для создания инструментов"""
    
    @staticmethod
    def create_all_tools() -> List[BaseTool]:
        """Создать все базовые инструменты"""
        return [
            FileTool(),
            PythonTool(),
            APITool(),
            DatabaseTool(),
            EmailTool()
        ]
    
    @staticmethod
    def create_tool(tool_name: str) -> Optional[BaseTool]:
        """Создать конкретный инструмент"""
        tools = {
            "file_tool": FileTool(),
            "python_tool": PythonTool(),
            "api_tool": APITool(),
            "database_tool": DatabaseTool(),
            "email_tool": EmailTool()
        }
        
        return tools.get(tool_name)
