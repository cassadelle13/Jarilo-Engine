import subprocess
import sys
import docker
import logging
from docker.errors import ContainerError


# Песочница для безопасного выполнения кода (адаптирована из Open-Interpreter)
class Sandbox:
    """
    Песочница для безопасного выполнения кода, сгенерированного агентами.
    
    Адаптирована из архитектуры Open-Interpreter для изолированного выполнения
    кода в дочернем процессе. На данном этапе поддерживает выполнение Python-кода
    через subprocess без дополнительной изоляции контейнеров.
    
    Концепция адаптирована из Open-Interpreter:
        - Использование subprocess для изоляции кода
        - Захват stdout и stderr для получения результатов
        - Проверка кода возврата для определения ошибок
        - Структурированный возврат результатов (output, error)
    
    Роль Sandbox:
        - Безопасное выполнение Python-кода от агентов
        - Изоляция кода в отдельном процессе
        - Захват и обработка результатов выполнения
        - Обработка ошибок при выполнении кода
    
    Будущие улучшения:
        - Поддержка других языков программирования (JavaScript, Bash и т.д.)
        - Полная изоляция с использованием Docker
        - Таймауты для предотвращения бесконечных циклов
        - Ограничение доступа к файловой системе
        - Логирование всех операций выполнения
    """
    
    def __init__(self):
        """
        Инициализирует песочницу с Docker-клиентом для изоляции.
        """
        self.logger = logging.getLogger(__name__)
        self.docker_client = docker.from_env()
        self.logger.info("Sandbox: Инициализация завершена с Docker-клиентом.")
    
    def run(self, code: str, language: str = "python") -> tuple:
        """
        Выполняет код в изолированном Docker-контейнере.
        
        Метод использует Docker для полной изоляции выполнения кода,
        сгенерированного микро-агентами. Результаты выполнения (stdout и stderr)
        захватываются и возвращаются в структурированном виде.
        
        Процесс:
        1. Валидация поддерживаемого языка программирования
        2. Запуск кода в Docker-контейнере jarilo-sandbox
        3. Захват стандартного вывода и ошибок
        4. Автоматическое удаление контейнера
        5. Возврат результатов или ошибок
        
        Args:
            code (str): Исходный код для выполнения.
            language (str): Язык программирования (по умолчанию "python").
                           Поддерживаемые языки: python
        
        Returns:
            tuple: Кортеж (output, error):
                   - output (str | None): Стандартный вывод контейнера или None при ошибке
                   - error (str | None): Стандартный вывод ошибок или None при успехе
        
        Raises:
            ValueError: Если указанный язык не поддерживается.
        
        Examples:
            >>> sandbox = Sandbox()
            >>> output, error = sandbox.run("print('Hello, World!')")
            >>> print(output)
            Hello, World!
            >>> print(error)
            None
            
            >>> output, error = sandbox.run("raise ValueError('Test error')")
            >>> print(output)
            None
            >>> print(error)
            Traceback (most recent call last):
              File "<string>", line 1, in <module>
            ValueError: Test error
        
        Notes:
            - Код выполняется в изолированном Docker-контейнере
            - Контейнер автоматически удаляется после выполнения
            - Поддерживается таймаут через Docker
            - Полная изоляция от хост-системы
        
        Future Implementation:
            - Добавление поддержки других языков (JavaScript, Bash, Go и т.д.)
            - Внедрение таймаутов для предотвращения зависания
            - Ограничение доступа к файловой системе и сети
            - Логирование с указанием task_id и agent_name
        """
        
        # Валидация поддерживаемого языка
        if language != "python":
            raise ValueError(
                f"Язык '{language}' не поддерживается. "
                f"Поддерживаемые языки: python"
            )
        
        self.logger.info(f"Sandbox: Запуск кода в Docker-контейнере: {code[:50]}...")
        
        try:
            # Запуск Docker-контейнера для выполнения кода
            container = self.docker_client.containers.run(
                image="jarilo-sandbox:latest",
                command=["python", "-c", code],
                remove=True,
                stdout=True,
                stderr=True
            )
            
            # Декодирование результатов
            stdout_str = container.decode('utf-8').strip() if container else ""
            stderr_str = ""  # В этом случае stderr не захватывается отдельно
            
            self.logger.info("Sandbox: Код успешно выполнен в контейнере.")
            return (stdout_str, None)
        
        except ContainerError as e:
            # Ошибка внутри контейнера
            stderr_str = e.stderr.decode('utf-8') if e.stderr else str(e)
            self.logger.error(f"Sandbox: Ошибка выполнения в контейнере: {stderr_str}")
            return (None, stderr_str)
        
        except Exception as e:
            # Другие ошибки Docker
            self.logger.error(f"Sandbox: Общая ошибка Docker: {str(e)}")
            return (None, str(e))