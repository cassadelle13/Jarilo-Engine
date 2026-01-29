import docker
import logging
from docker.errors import APIError, NotFound


# Менеджер Docker Volumes для управления рабочими пространствами агентов
class VolumeManager:
    """
    Менеджер Docker Volumes для Jarilo.
    
    Класс отвечает за управление Docker Volumes, которые используются
    в качестве изолированных рабочих пространств для агентов. Каждой задаче
    выделяется отдельный том для хранения файлов, исходного кода и результатов
    выполнения. Менеджер создает, управляет и удаляет эти тома.
    
    Использует docker-py для взаимодействия с Docker API и обеспечивает
    надежное управление жизненным циклом томов.
    
    Роль VolumeManager:
        - Создание Docker Volumes для каждой задачи
        - Управление жизненным циклом томов
        - Изоляция рабочих пространств различных агентов
        - Очистка ресурсов после завершения задачи
        - Обеспечение безопасности и изоляции данных
    
    Логирование:
        - Все операции логируются для отладки и мониторинга
        - Ошибки логируются с подробной информацией
    
    Attributes:
        client (docker.client.DockerClient): Клиент Docker для управления томами.
        logger (logging.Logger): Логгер для записи операций.
    """
    
    def __init__(self):
        """
        Инициализирует менеджер томов и подключается к Docker демону.
        
        Создает подключение к локальному Docker демону и инициализирует логгер.
        
        Raises:
            docker.errors.DockerException: Если не удается подключиться к Docker демону.
        """
        try:
            self.client = docker.from_env()
            self.logger = logging.getLogger(__name__)
            self.logger.info("VolumeManager инициализирован")
        except Exception as e:
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Ошибка при инициализации VolumeManager: {str(e)}")
            raise
    
    def create_workspace(self, task_id: str):
        """
        Создает Docker Volume (рабочее пространство) для задачи.
        
        Создает отдельный том для каждой задачи, в котором будут
        храниться все файлы, исходный код и результаты выполнения.
        Это обеспечивает изоляцию между задачами и безопасность данных.
        
        Процесс:
        1. Формирование имени тома на основе task_id
        2. Создание тома через Docker API
        3. Логирование успешного создания
        4. Возврат имени тома
        
        Args:
            task_id (str): Уникальный идентификатор задачи.
        
        Returns:
            str: Имя созданного Docker Volume в формате "jarilo_workspace_{task_id}".
            None: Если произошла ошибка при создании.
        
        Notes:
            - Имя тома включает префикс "jarilo_workspace_" для идентификации
            - Каждый том привязан к уникальной задаче через task_id
            - Том создается с параметрами по умолчанию Docker
        
        Future Implementation:
            - Добавление лейблов (labels) с метаданными задачи
            - Конфигурация драйвера тома
            - Установка квот на размер тома
        """
        # Формирование имени тома
        volume_name = f"jarilo_workspace_{task_id}"
        
        try:
            # Создание Docker Volume
            self.client.volumes.create(name=volume_name)
            
            # Логирование успешного создания
            self.logger.info(f"Создан Docker Volume: {volume_name}")
            
            return volume_name
        
        except APIError as e:
            # Обработка ошибок Docker API
            self.logger.error(
                f"Ошибка Docker API при создании тома '{volume_name}': {str(e)}"
            )
            return None
        
        except Exception as e:
            # Обработка неожиданных ошибок
            self.logger.error(
                f"Неожиданная ошибка при создании тома '{volume_name}': {str(e)}"
            )
            return None
    
    def cleanup_workspace(self, volume_name: str):
        """
        Удаляет Docker Volume после завершения задачи.
        
        Очищает рабочее пространство и освобождает ресурсы после
        завершения выполнения задачи. Удаляет все файлы и данные,
        связанные с этим томом. Параметр force=True гарантирует удаление
        даже если том используется контейнером.
        
        Процесс:
        1. Получение объекта тома по имени
        2. Удаление тома с параметром force=True
        3. Логирование успешного удаления
        
        Args:
            volume_name (str): Имя Docker Volume для удаления.
        
        Returns:
            bool: True если удаление успешно, False при ошибке.
        
        Notes:
            - force=True позволяет удалить том, даже если он используется контейнером
            - Это важно для гарантированной очистки ресурсов после задачи
            - Операция необратима - данные будут полностью удалены
        
        Future Implementation:
            - Добавление резервного копирования перед удалением
            - Логирование размера удаляемого тома
            - Метрики использования дискового пространства
        """
        try:
            # Получение объекта тома
            volume = self.client.volumes.get(volume_name)
            
            # Удаление тома с force=True
            volume.remove(force=True)
            
            # Логирование успешного удаления
            self.logger.info(f"Удален Docker Volume: {volume_name}")
            
            return True
        
        except NotFound:
            # Том не найден
            self.logger.warning(
                f"Docker Volume не найден при удалении: {volume_name}"
            )
            return False
        
        except APIError as e:
            # Ошибки Docker API при удалении
            self.logger.error(
                f"Ошибка Docker API при удалении тома '{volume_name}': {str(e)}"
            )
            return False
        
        except Exception as e:
            # Обработка неожиданных ошибок
            self.logger.error(
                f"Неожиданная ошибка при удалении тома '{volume_name}': {str(e)}"
            )
            return False