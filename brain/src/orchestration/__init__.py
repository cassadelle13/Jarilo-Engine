"""
Пакет orchestration - оркестрация выполнения задач в Jarilo.

Архитектура перестроена на LangGraph в graph.py.
"""

from .graph import compiled_graph

__all__ = ["compiled_graph"]