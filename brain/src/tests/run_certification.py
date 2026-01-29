"""
Скрипт сертификации TaskPlanner.
Прогоняет канареечные промпты и оценивает качество планирования.
"""

import asyncio
import sys
import os

# Добавление пути к brain/src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestration.planner import TaskPlanner
from tests.canary_prompts import CANARY_SUITE
from tests.evaluator import evaluate_plan


async def run_certification():
    """
    Запускает сертификацию TaskPlanner на канареечных промптах.
    """
    print("=" * 60)
    print("СЕРТИФИКАЦИЯ TASKPLANNER")
    print("=" * 60)

    # Инициализация планировщика
    planner = TaskPlanner()

    results = []
    passed = 0
    total = len(CANARY_SUITE)

    for i, canary in enumerate(CANARY_SUITE, 1):
        print(f"\n[{i}/{total}] Тестирование: {canary['name']}")
        print(f"Промпт: {canary['prompt'][:60]}{'...' if len(canary['prompt']) > 60 else ''}")

        try:
            # Генерация плана
            plan = await planner.create_plan(canary['prompt'])
            print(f"План сгенерирован: {len(plan)} шагов")

            # Оценка плана
            if isinstance(plan, list):
                # Преобразование списка в JSON-строку для оценки
                import json
                response_text = json.dumps(plan, ensure_ascii=False)
            else:
                response_text = str(plan)

            metrics = evaluate_plan(response_text)

            # Проверка критериев
            is_passed = (
                metrics["is_valid_json"] and
                not metrics["has_wrapper_text"] and
                metrics["step_count"] > 0 and
                metrics["atomicity_score"] >= 0.5 and
                metrics["clarity_score"] >= 0.3
            )

            if is_passed:
                passed += 1
                status = "✓ ПРОЙДЕН"
            else:
                status = "✗ ПРОВАЛЕН"

            print(f"Статус: {status}")
            print(f"Метрики: JSON={metrics['is_valid_json']}, Обертка={metrics['has_wrapper_text']}, "
                  f"Шаги={metrics['step_count']}, Атомарность={metrics['atomicity_score']:.2f}, "
                  f"Ясность={metrics['clarity_score']:.2f}")

            results.append({
                "name": canary["name"],
                "passed": is_passed,
                "metrics": metrics
            })

        except Exception as e:
            print(f"✗ ОШИБКА: {str(e)}")
            results.append({
                "name": canary["name"],
                "passed": False,
                "error": str(e)
            })

    # Итоговый отчет
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    print(f"Всего тестов: {total}")
    print(f"Пройдено: {passed}")
    print(f"Провалено: {total - passed}")
    print(".1f")

    if passed == total:
        print("🎉 СЕРТИФИКАЦИЯ ПРОЙДЕНА!")
        return 0
    else:
        print("❌ СЕРТИФИКАЦИЯ ПРОВАЛЕНА!")
        for result in results:
            if not result.get("passed", False):
                print(f"  - {result['name']}: {'Ошибка: ' + result.get('error', 'Не прошел метрики')}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_certification())
    sys.exit(exit_code)