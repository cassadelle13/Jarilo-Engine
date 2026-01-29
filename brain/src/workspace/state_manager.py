import uuid
import logging
import asyncio
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from orm import Task, Step, get_db_session


# Менеджер состояния - управляет сохранением и обновлением состояния задач
class StateManager:
    """
    Менеджер состояния для Jarilo.

    Класс отвечает за управление состоянием всех задач в системе.
    Использует SQLAlchemy ORM для хранения и управления данными о задачах,
    их статусах, планах и результатах выполнения. Обеспечивает
    персистентность данных между запусками приложения.

    Основные операции:
        - Создание новых задач с уникальными ID
        - Обновление статуса выполнения задач
        - Получение информации о существующих задачах
        - Сохранение плана выполнения задачи

    Роль StateManager:
        - Сохранение информации о задачах в базу данных
        - Получение данных о существующих задачах
        - Обновление статуса выполнения задач
        - Управление состоянием экосистемы Jarilo
        - Обеспечение надежности и консистентности данных

    Attributes:
        logger (logging.Logger): Логгер для записи операций.
    """

    def __init__(self):
        """
        Инициализирует менеджер состояния.

        Notes:
            - Использует SQLAlchemy для работы с базой данных
            - Все операции выполняются асинхронно
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("StateManager: Инициализация с SQLAlchemy ORM...")
    
    async def create_task(self, prompt: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Создает новую задачу в системе и сохраняет ее в базу данных.

        Генерирует уникальный ID для задачи, инициализирует все необходимые
        поля (статус, план) и сохраняет задачу в SQLAlchemy.

        Процесс:
        1. Генерация уникального task_id с помощью UUID
        2. Создание Task объекта с начальными значениями
        3. Сохранение задачи в базу данных
        4. Возврат полных данных задачи

        Args:
            prompt (str): Описание задачи от пользователя.
            workspace_id (Optional[str]): ID рабочего пространства.

        Returns:
            dict: Словарь с полными данными созданной задачи:
                  {
                      "id": str,          # UUID уникальный идентификатор
                      "prompt": str,      # Исходное описание задачи
                      "status": str,      # Начальный статус "created"
                      "plan": list        # Пустой список для плана выполнения
                  }

        Notes:
            - ID генерируется автоматически и гарантирует уникальность
            - Начальный статус всегда "created"
            - План заполняется позже после работы "Стратега"
        """
        # Генерация уникального ID для задачи
        task_id = str(uuid.uuid4())

        async for session in get_db_session():
            # Создание новой задачи
            task = Task(
                task_id=task_id,
                description=prompt,
                status="created",
                workspace_id=workspace_id
                # user_id убран - он optional и вызывает проблемы с SQLAlchemy
            )

            session.add(task)
            await session.commit()  # Явно коммитим изменения

            self.logger.info(f"StateManager: Создана задача {task_id}")

            # Возврат данных в формате, совместимом со старым API
            return {
                "id": task.task_id,
                "prompt": task.description,
                "status": task.status,
                "plan": []
            }
    
    async def update_task_status(self, task_id: str, new_status: str) -> bool:
        """
        Обновляет статус выполнения задачи.

        Находит задачу по ID и обновляет ее статус на новое значение.
        Используется для отслеживания прогресса выполнения задачи
        на разных этапах обработки.

        Типичные статусы:
            - "created": Задача создана, ожидает обработки
            - "planning": Стратег создает план выполнения
            - "executing": Тактик выполняет план
            - "completed": Задача успешно выполнена
            - "failed": Ошибка при выполнении задачи

        Args:
            task_id (str): UUID уникальный идентификатор задачи.
            new_status (str): Новый статус для задачи.

        Returns:
            bool: True если обновление успешно, False если задача не найдена.

        Notes:
            - Операция обновления атомарна
            - Старые данные задачи сохраняются, изменяется только статус
        """
        async for session in get_db_session():
            stmt = (
                update(Task)
                .where(Task.task_id == task_id)
                .values(status=new_status)
            )
            result = await session.execute(stmt)
            success = result.rowcount > 0

            if success:
                self.logger.info(f"StateManager: Статус задачи {task_id} обновлен на {new_status}")
            else:
                self.logger.warning(f"StateManager: Задача {task_id} не найдена для обновления статуса")

            await session.commit()
            return success
    
    async def update_task_plan(self, task_id: str, plan) -> bool:
        """
        Обновляет план выполнения задачи в базе данных.

        Создает Step объекты для каждого пункта плана.

        Args:
            task_id (str): UUID задачи.
            plan: План выполнения (str или list). Будет нормализован к List[str].

        Returns:
            bool: True если обновление успешно.

        Raises:
            ValueError: Если plan не может быть нормализован к List[str].
        """
        # Нормализация плана к List[str]
        if isinstance(plan, str):
            normalized_plan = [plan]
        elif isinstance(plan, list):
            normalized_plan = []
            for item in plan:
                if isinstance(item, str):
                    normalized_plan.append(item)
                elif isinstance(item, dict):
                    normalized_plan.append(json.dumps(item, ensure_ascii=False))
                else:
                    raise ValueError(f"Элементы плана должны быть str или dict, получено: {type(item)}")
        else:
            raise ValueError(f"План должен быть str или list, получено: {type(plan)}")

        self.logger.debug(f"StateManager: Нормализован план для задачи {task_id}: {normalized_plan[:2]}...")

        async for session in get_db_session():
            # Найти задачу
            stmt = select(Task).where(Task.task_id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                self.logger.warning(f"StateManager: Задача {task_id} не найдена для обновления плана")
                return False

            # Удалить существующие шаги
            await session.execute(delete(Step).where(Step.task_id == task.id))

            # Создать новые шаги
            for i, step_desc in enumerate(normalized_plan):
                step = Step(
                    step_id=str(uuid.uuid4()),
                    task_id=task.id,
                    description=step_desc,
                    status="pending",
                    order=i
                )
                session.add(step)

            self.logger.info(f"StateManager: План задачи {task_id} обновлен с {len(normalized_plan)} шагами")
            await session.commit()
            return True
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает полные данные задачи из базы данных по ID.

        Ищет задачу с указанным ID и возвращает всю информацию о ней,
        включая промпт, статус, план и другие метаданные.

        Args:
            task_id (str): UUID уникальный идентификатор задачи.

        Returns:
            dict: Словарь с полными данными задачи или None, если не найдена:
                  {
                      "id": str,          # UUID идентификатор
                      "prompt": str,      # Исходное описание задачи
                      "status": str,      # Текущий статус
                      "plan": list        # План выполнения из шагов
                      "result": str       # Объединенные результаты шагов
                  }

        Notes:
            - Поиск выполняется по полю "task_id" в базе данных
            - Возвращается только первая найденная задача
        """
        async for session in get_db_session():
            stmt = (
                select(Task)
                .options(selectinload(Task.steps))
                .where(Task.task_id == task_id)
            )
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return None

            # Получить план из шагов
            plan = [step.description for step in sorted(task.steps, key=lambda s: s.order)]

            # Получить результаты из завершенных шагов как List[str]
            result_list = []
            for step in sorted(task.steps, key=lambda s: s.order):
                if step.result:
                    result_list.append(str(step.result))

            return {
                "id": task.task_id,
                "prompt": task.description,
                "status": task.status,
                "plan": plan,
                "result": result_list  # List[str] как в schema
            }
    
    async def add_step_result(self, task_id: str, result) -> bool:
        """
        Добавляет результат выполнения шага к задаче в базе данных.

        Находит соответствующий шаг по описанию и обновляет его результат.

        Args:
            task_id (str): UUID уникальный идентификатор задачи.
            result: Результат выполнения шага. Может быть dict или str.

        Returns:
            bool: True если обновление успешно.
        """
        # Обработка случая, когда result - строка (для обратной совместимости)
        if isinstance(result, str):
            self.logger.warning(f"add_step_result получил строку вместо dict: {result[:100]}...")
            # Создаем фиктивный результат для сохранения
            result = {
                "step": {"description": "Execution result"},
                "status": "completed",
                "output": result
            }

        step_description = result.get("step", {}).get("description")
        if not step_description:
            self.logger.warning(f"StateManager: Отсутствует описание шага в результате для задачи {task_id}")
            return False

        status = result.get("status", "completed")
        output = result.get("output", "")

        async for session in get_db_session():
            # Найти задачу
            stmt = select(Task).where(Task.task_id == task_id)
            result_task = await session.execute(stmt)
            task = result_task.scalar_one_or_none()

            if not task:
                self.logger.warning(f"StateManager: Задача {task_id} не найдена")
                return False

            # Найти шаг по описанию
            stmt = select(Step).where(
                (Step.task_id == task.id) &
                (Step.description == step_description)
            )
            result_step = await session.execute(stmt)
            step = result_step.scalar_one_or_none()

            if not step:
                max_order_stmt = select(func.max(Step.order)).where(Step.task_id == task.id)
                max_order_result = await session.execute(max_order_stmt)
                max_order = max_order_result.scalar_one_or_none()
                next_order = int(max_order) + 1 if max_order is not None else 0

                step = Step(
                    step_id=str(uuid.uuid4()),
                    task_id=task.id,
                    description=step_description,
                    status=status,
                    order=next_order,
                    result=output,
                )
                session.add(step)
                self.logger.info(f"StateManager: Создан новый шаг '{step_description}' для задачи {task_id}")
                await session.commit()
                return True

            # Обновить шаг
            step.status = status
            step.result = output

            self.logger.info(f"StateManager: Результат шага '{step_description}' добавлен для задачи {task_id}")
            await session.commit()
            return True