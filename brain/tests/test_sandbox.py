import pytest
from security.sandbox import Sandbox


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