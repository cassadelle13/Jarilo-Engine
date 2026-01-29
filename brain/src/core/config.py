import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


# Конфигурация приложения Jarilo с поддержкой переменных окружения
class Settings(BaseSettings):
    """
    Конфигурация приложения Jarilo.
    
    Класс управляет всеми настройками приложения с поддержкой загрузки
    из переменных окружения и файла .env. Использует pydantic-settings
    для автоматической валидации и типизации конфигурационных параметров.
    
    Процесс загрузки конфигурации:
    1. Сначала ищутся переменные окружения с совпадающими названиями
    2. Затем загружаются значения из .env файла
    3. Если переменная не найдена, используется значение по умолчанию
    
    Преимущества использования BaseSettings:
        - Автоматическое чтение переменных окружения
        - Загрузка из .env файла для локальной разработки
        - Типизированная валидация всех параметров
        - Переопределение значений через переменные окружения в production
    
    Атрибуты:
        PROJECT_NAME (str): Название проекта.
        API_V1_STR (str): Префикс пути для API v1.
        DB_FILE (str): Путь к файлу базы данных состояния.
        OPENAI_API_KEY (str): API ключ OpenAI для взаимодействия с LLM.
        HTTP_TRUST_ENV (bool): Whether HTTP clients should trust environment/system proxy settings.
    """
    
    PROJECT_NAME: str = "Jarilo Brain"
    API_V1_STR: str = "/api/v1"
    DB_FILE: str = Field("data/jarilo_state.db", description="Путь к файлу базы данных состояния.")
    OPENAI_API_KEY: str = Field(default="test-key", description="API-ключ для доступа к OpenAI.")
    HTTP_TRUST_ENV: bool = Field(default=True, description="Whether HTTP clients should trust environment/system proxy settings.")
    ENCRYPTION_KEY: str = Field(default_factory=lambda: os.environ.get('JARILO_ENCRYPTION_KEY', ''), description="Ключ шифрования для секретов пользователей.")
    JARILO_AGENT_IMAGE: str = "jarilo-ecosystem-agent:latest"
    WORKSPACES_ROOT: str = Field("/host_workspaces", description="Корневая директория для рабочих пространств задач.")
    JARILO_ENCRYPTION_KEY: str = Field(default="", description="Main encryption key for secrets (alias for ENCRYPTION_KEY)")
    WORKSPACES_HOST_ROOT: str = Field(default_factory=lambda: os.environ.get('HOST_WORKSPACE_ROOT', '/tmp/workspaces' if os.name != 'nt' else 'C:\\tmp\\workspaces'), description="Host path для рабочих пространств.")
    BOOTSTRAP_TOKEN: str = Field(default_factory=lambda: os.environ.get('JARILO_BOOTSTRAP_TOKEN', ''), description="Optional token to protect one-time bootstrap endpoints.")
    
    class Config:
        """
        Конфигурация для BaseSettings.
        
        Параметры:
            env_file (str): Путь к файлу .env для загрузки переменных окружения.
            env_file_encoding (str): Кодировка файла .env.
        """
        env_file = str(Path(__file__).resolve().parents[3] / ".env")
        env_file_encoding = "utf-8"


# Глобальный экземпляр конфигурации (singleton)
# Используется во всем приложении через импорт: from core.config import settings
settings = Settings()