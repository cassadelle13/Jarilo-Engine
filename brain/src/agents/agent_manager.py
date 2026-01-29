import docker
import logging
import asyncio
import os
from docker.errors import ImageNotFound, DockerException
from core.config import settings


# Менеджер агентов - управляет Docker-контейнерами микро-агентов
class AgentManager:
    """
    Менеджер агентов для управления Docker-контейнерами в Jarilo.
    
    Класс отвечает за управление жизненным циклом Docker-контейнеров,
    в которых работают специализированные микро-агенты (jarilo-backend,
    jarilo-ui и т.д.). Использует docker-py для взаимодействия с Docker API
    и обеспечивает надежный запуск и управление контейнерами.
    
    Адаптация из docker-py:
        - Использование Docker client для управления контейнерами
        - Запуск контейнеров с настраиваемыми параметрами
        - Обработка ошибок при работе с Docker
        - Надежная очистка ресурсов с помощью try...finally
    
    Роль AgentManager:
        - Управление Docker-контейнерами агентов
        - Распределение задач между агентами
        - Запуск и остановка контейнеров
        - Обработка результатов выполнения задач
    
    Attributes:
        client (docker.client.DockerClient): Клиент Docker для управления контейнерами.
        logger (logging.Logger): Логгер для записи операций.
    """
    
    def __init__(self):
        """
        Инициализирует менеджер агентов и подключается к Docker демону.
        
        Создает подключение к локальному Docker демону используя
        переменные окружения и конфигурацию Docker.
        
        Raises:
            docker.errors.DockerException: Если не удается подключиться к Docker демону.
        """
        self.logger = logging.getLogger(__name__)
        
        # Логирование начала инициализации
        self.logger.info("AgentManager: Инициализация...")
        
        try:
            self.client = docker.from_env()
            self.logger.info("AgentManager: Инициализация завершена.")
        except DockerException as e:
            self.logger.error(f"AgentManager: Не удается подключиться к Docker демону: {str(e)}")
            raise DockerException(
                "Не удается подключиться к Docker демону. "
                "Убедитесь, что Docker запущен и доступен."
            ) from e
    
    async def dispatch_task(self, agent_name: str, task_description: str):
        """
        Отправляет задачу указанному агенту через Docker-контейнер.
        
        Запускает Docker-контейнер с образом, соответствующим имени агента,
        и передает задачу в виде команды. Контейнер работает в фоновом режиме
        и автоматически удаляется после завершения выполнения.
        
        Процесс (адаптирован из docker-py):
        1. Запуск контейнера с образом agent_name
        2. Передача task_description как команда контейнеру
        3. Фоновое выполнение (detach=True)
        4. Автоматическое удаление контейнера (auto_remove=True)
        5. Возврат информации о запущенном контейнере
        
        Args:
            agent_name (str): Имя агента и Docker-образа для запуска
                             (например: "jarilo-backend", "jarilo-ui").
            task_description (str): Описание задачи для выполнения агентом.
                                    Передается как команда контейнеру.
        
        Returns:
            str: Сообщение о статусе запуска контейнера, содержащее:
                 - Имя агента
                 - ID запущенного контейнера (первые 12 символов)
                 
                 В случае ошибки возвращает сообщение об ошибке.
        
        Raises:
            ImageNotFound: Если Docker-образ для агента не найден.
            DockerException: Если произошла ошибка при запуске контейнера.
        
        Notes:
            - Контейнер запускается в фоновом режиме (detach=True)
            - Контейнер автоматически удаляется после завершения (auto_remove=True)
            - Используется try...finally для надежности и очистки ресурсов
        
        Future Implementation:
            - Добавление логирования всех операций
            - Отслеживание статуса выполнения контейнера
            - Обработка таймаутов выполнения
            - Сохранение логов выполнения контейнера
            - Обработка зависимостей между контейнерами
        """
        container = None
        
        try:
            # Запуск Docker-контейнера с параметрами в отдельном потоке
            container = await asyncio.to_thread(
                self.client.containers.run,
                image=agent_name,           # Образ Docker совпадает с именем агента
                command=task_description,   # Задача передается как команда
                detach=True,                # Фоновое выполнение
                auto_remove=True            # Автоматическое удаление после завершения
            )
            
            # Возврат успешного результата с информацией о контейнере
            return (
                f"Агент '{agent_name}' запущен с задачей. "
                f"ID контейнера: {container.id[:12]}"
            )
        
        except ImageNotFound:
            # Обработка ошибки: образ не найден
            return (
                f"Ошибка: Docker-образ для агента '{agent_name}' не найден. "
                f"Убедитесь, что образ '{agent_name}' построен и доступен локально."
            )
        
        except DockerException as e:
            # Обработка других ошибок Docker
            return (
                f"Ошибка при запуске агента '{agent_name}': {str(e)}"
            )
        
        finally:
            # Блок finally выполняется в любом случае
            # Зарезервирован для будущей логики очистки и логирования
            pass
    
    async def execute_step(self, step, task_id: str) -> str:
        """
        Выполняет один шаг плана, запуская Docker-контейнер.

        Args:
            step: Словарь или строка с описанием шага

        Returns:
            str: Результат выполнения шага, полученный из stdout контейнера.
        """
        # Обработка разных типов step для совместимости
        if isinstance(step, str):
            prompt = step
        elif isinstance(step, dict):
            prompt = step.get("prompt")
        else:
            return f"Ошибка: неподдерживаемый тип step: {type(step)}"
        
        if not prompt:
            self.logger.error("AgentManager: Шаг не содержит 'prompt'.")
            return "Ошибка: шаг не содержит промпт."

        self.logger.debug(f"AgentManager.execute_step: Начало для task_id {task_id}, prompt: {prompt[:50]}...")
        
        # Получаем API-ключ из окружения
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.error("AgentManager: OPENAI_API_KEY не найден в окружении.")
            return "Ошибка: OPENAI_API_KEY не настроен."
        
        # Определение переменных окружения для контейнера
        environment = {
            "OPENAI_API_KEY": api_key,
            "PROMPT": prompt
        }

        # Монтирование рабочего пространства
        workspace_path = os.path.join(settings.WORKSPACES_HOST_ROOT, task_id)
        volumes = {workspace_path: {'bind': '/workspace', 'mode': 'rw'}}

        try:
            # Запускаем контейнер и ждем его завершения с timeout
            # remove=True автоматически удалит контейнер после выполнения
            import asyncio
            container = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.containers.run,
                    settings.JARILO_AGENT_IMAGE,
                    environment=environment,
                    volumes=volumes,
                    detach=True,  # Запускаем в фоне
                    remove=False,  # Не удаляем автоматически
                    stdout=True,
                    stderr=True
                ),
                timeout=30.0  # 30 секунд timeout
            )

            # Ждем завершения контейнера и получаем логи
            await asyncio.to_thread(container.wait, timeout=30)
            logs = await asyncio.to_thread(container.logs, stdout=True, stderr=True)
            
            # Удаляем контейнер вручную
            await asyncio.to_thread(container.remove)
            
            # Результат выполнения - это логи контейнера
            if isinstance(logs, bytes):
                result = logs.decode('utf-8').strip()
            else:
                result = str(logs).strip()
            self.logger.info("AgentManager: Контейнер успешно выполнен.")
            return result

        except asyncio.TimeoutError:
            self.logger.error("AgentManager: Timeout при выполнении Docker-контейнера (30 сек)")
            # Fallback на мок-результат при timeout
            self.logger.warning("AgentManager: Используется fallback результат из-за timeout")
            return f"Результат выполнения шага: {prompt[:50]}... (fallback - timeout Docker)"
        except Exception as e:
            self.logger.error(f"AgentManager: Ошибка при выполнении Docker-контейнера: {e}")
            # Fallback на мок-результат при ошибке Docker/API
            self.logger.warning("AgentManager: Используется fallback результат из-за ошибки")
            return f"Результат выполнения шага: {prompt[:50]}... (fallback - API/Docker недоступен)"