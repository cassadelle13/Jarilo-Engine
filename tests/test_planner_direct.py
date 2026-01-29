import asyncio
import os
import sys

# Добавляем путь к brain
sys.path.insert(0, 'brain/src')

from orchestration.planner import TaskPlanner

async def test_planner():
    print("Тестирование планировщика...")

    planner = TaskPlanner()

    prompt = """Создай файл test_output.txt со следующим содержимым:
```python
with open('test_output.txt', 'w') as f:
    f.write('Тест прошел успешно!')
```

Затем проверь, что файл создан."""

    try:
        plan = await planner.create_plan(prompt)
        print(f"План: {plan}")
        print(f"Тип плана: {type(plan)}")
        if isinstance(plan, list):
            for i, step in enumerate(plan):
                print(f"Шаг {i+1}: {step}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_planner())