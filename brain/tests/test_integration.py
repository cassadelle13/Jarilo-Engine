import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app  # Предполагаем, что main.py в brain/src
from security.sandbox import Sandbox


@pytest.fixture
def client():
    return TestClient(app)


def test_sandbox_execution():
    """Тест выполнения кода в песочнице через Docker."""
    sandbox = Sandbox()

    # Тест простого кода
    output, error = sandbox.run("print('Hello, Sandbox!')")

    assert output == "Hello, Sandbox!"
    assert error is None

    # Тест кода с ошибкой
    output, error = sandbox.run("raise ValueError('Test error')")

    assert output is None
    assert "ValueError: Test error" in error


@pytest.mark.asyncio
async def test_create_and_run_task(client):
    """Интеграционный тест создания и выполнения задачи."""
    # Создание задачи
    response = client.post("/api/v1/tasks/", json={"prompt": "Напиши короткое стихотворение о коде."})
    assert response.status_code == 200

    task_data = response.json()
    task_id = task_data["task_id"]

    # Ожидание выполнения (упрощенная версия)
    await asyncio.sleep(5)  # Подождать выполнения

    # Получение статуса
    status_response = client.get(f"/api/v1/tasks/{task_id}")
    assert status_response.status_code == 200

    status_data = status_response.json()
    assert status_data["status"] == "completed"
    assert "result" in status_data