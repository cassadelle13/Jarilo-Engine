"""
Оценщик планов TaskPlanner.
Функции для анализа качества сгенерированных планов.
"""

import json
import re


def evaluate_plan(response_text: str) -> dict:
    """
    Оценивает план на основе метрик качества.

    Args:
        response_text (str): Текст ответа от TaskPlanner (ожидается JSON-массив строк).

    Returns:
        dict: Словарь с метриками:
            - is_valid_json (bool): Валидный ли JSON.
            - has_wrapper_text (bool): Есть ли обертывающий текст вокруг JSON.
            - step_count (int): Количество шагов в плане.
            - avg_step_length (float): Средняя длина шага в символах.
            - atomicity_score (float): Оценка атомарности шагов (0-1).
            - clarity_score (float): Оценка ясности (0-1).
    """
    metrics = {
        "is_valid_json": False,
        "has_wrapper_text": False,
        "step_count": 0,
        "avg_step_length": 0.0,
        "atomicity_score": 0.0,
        "clarity_score": 0.0
    }

    # Проверка на валидный JSON
    try:
        parsed = json.loads(response_text.strip())
        if isinstance(parsed, list) and all(isinstance(step, str) for step in parsed):
            metrics["is_valid_json"] = True
            steps = parsed
        else:
            return metrics  # Не массив строк
    except json.JSONDecodeError:
        # Проверка на обертывающий текст
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, list) and all(isinstance(step, str) for step in parsed):
                    metrics["is_valid_json"] = True
                    metrics["has_wrapper_text"] = True
                    steps = parsed
                else:
                    return metrics
            except json.JSONDecodeError:
                return metrics
        else:
            return metrics

    # Анализ шагов
    if steps:
        metrics["step_count"] = len(steps)
        lengths = [len(step) for step in steps]
        metrics["avg_step_length"] = sum(lengths) / len(lengths)

        # Оценка атомарности: шаги должны быть короткими и начинаться с глагола
        atomic_scores = []
        for step in steps:
            score = 0
            if 20 <= len(step) <= 200:  # Оптимальная длина
                score += 0.5
            if re.match(r'^[А-Яа-яA-Za-z]', step):  # Начинается с буквы (не цифры)
                score += 0.5
            atomic_scores.append(score)
        metrics["atomicity_score"] = sum(atomic_scores) / len(atomic_scores) if atomic_scores else 0

        # Оценка ясности: наличие артефактов (файлы, команды)
        clarity_scores = []
        for step in steps:
            score = 0
            if re.search(r'\.(html|css|js|py|json)', step, re.IGNORECASE):  # Файлы
                score += 0.5
            if 'создать' in step.lower() or 'написать' in step.lower() or 'добавить' in step.lower():
                score += 0.5
            clarity_scores.append(score)
        metrics["clarity_score"] = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0

    # Общая оценка
    metrics["total_score"] = (metrics["atomicity_score"] + metrics["clarity_score"]) / 2

    return metrics