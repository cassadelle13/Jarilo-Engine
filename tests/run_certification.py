"""
Certification test runner for TaskPlanner.
Runs canary prompts and evaluates results.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'brain', 'src'))

from orchestration.planner import TaskPlanner
from tests.canary_prompts import CANARY_SUITE
from tests.evaluator import evaluate_plan


async def run_certification():
    """Run certification tests for TaskPlanner."""
    print("Запуск сертификации TaskPlanner")
    print("=" * 50)

    # Initialize planner
    planner = TaskPlanner()

    results = []
    total_score = 0

    for i, canary in enumerate(CANARY_SUITE, 1):
        print(f"\n[{i}/{len(CANARY_SUITE)}] Тестирование: {canary['name']}")
        print(f"Prompt: {canary['prompt']}")
        print(f"Trap: {canary['trap']}")

        try:
            # Generate plan
            plan_json = await planner.create_plan(canary['prompt'])
            print(f"Plan: {plan_json}")

            # Evaluate
            metrics = evaluate_plan(plan_json)
            score = metrics['total_score']
            total_score += score

            status = "PASS" if score >= 0.4 else "FAIL"
            print(f"Результат: {status} (Score: {score:.2f})")

            results.append({
                "name": canary['name'],
                "score": score,
                "passed": score >= 0.4,
                "metrics": metrics
            })

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "name": canary['name'],
                "score": 0,
                "passed": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ СЕРТИФИКАЦИИ")
    print("=" * 50)

    passed_count = sum(1 for r in results if r['passed'])
    avg_score = total_score / len(results)

    print(f"Пройдено тестов: {passed_count}/{len(results)}")
    print(f"Средний балл: {avg_score:.2f}")

    if avg_score >= 0.4:
        print("СЕРТИФИКАЦИЯ ПРОЙДЕНА!")
        return True
    else:
        print("СЕРТИФИКАЦИЯ НЕ ПРОЙДЕНА!")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_certification())
    sys.exit(0 if success else 1)