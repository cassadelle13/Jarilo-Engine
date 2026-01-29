"""
Evaluator for assessing plan quality from TaskPlanner.
"""

import json
import re


def evaluate_plan(plan_json: str) -> dict:
    """
    Evaluate the quality of a generated plan.

    Args:
        plan_json: JSON string representing the plan

    Returns:
        dict: Evaluation metrics
    """
    try:
        plan = json.loads(plan_json)
    except json.JSONDecodeError:
        return {
            "valid_json": False,
            "atomicity_score": 0,
            "clarity_score": 0,
            "total_score": 0
        }

    # Check if plan has required structure
    if not isinstance(plan, list):
        return {
            "valid_json": True,
            "atomicity_score": 0,
            "clarity_score": 0,
            "total_score": 0
        }

    atomicity_score = 0
    clarity_score = 0

    for step in plan:
        if not isinstance(step, dict):
            continue

        # Check for required fields
        if "description" in step and "command" in step:
            clarity_score += 1

        # Check atomicity - steps should be simple
        command = step.get("command", "")
        if len(command.split()) <= 5:  # Simple commands
            atomicity_score += 1

    total_steps = len(plan)
    if total_steps == 0:
        return {
            "valid_json": True,
            "atomicity_score": 0,
            "clarity_score": 0,
            "total_score": 0
        }

    return {
        "valid_json": True,
        "atomicity_score": atomicity_score / total_steps,
        "clarity_score": clarity_score / total_steps,
        "total_score": (atomicity_score + clarity_score) / (2 * total_steps)
    }