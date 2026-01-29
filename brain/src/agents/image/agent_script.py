import os
import sys
from openai import OpenAI

def main():
    """
    Главная функция скрипта-агента.
    """
    print("--- Агент: Скрипт запущен. ---", file=sys.stderr)

    # Шаг 1: Получение данных из переменных окружения
    api_key = os.getenv("OPENAI_API_KEY")
    prompt = os.getenv("PROMPT")

    if not api_key or not prompt:
        print("--- Агент: Ошибка! Переменные окружения OPENAI_API_KEY и PROMPT должны быть установлены. ---", file=sys.stderr)
        sys.exit(1)

    print(f"--- Агент: Получен промпт: {prompt[:50]}... ---", file=sys.stderr)

    # Шаг 2: Инициализация клиента OpenAI
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"--- Агент: Ошибка при инициализации клиента OpenAI: {e} ---", file=sys.stderr)
        sys.exit(1)

    # Шаг 3: Обращение к API OpenAI
    try:
        print("--- Агент: Отправка запроса к OpenAI... ---", file=sys.stderr)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Your task is to directly execute the user's request.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4.1-mini",
        )
        # Результат выводим в stdout, чтобы его мог прочитать вызывающий процесс
        result = chat_completion.choices[0].message.content
        print(result)

    except Exception as e:
        print(f"--- Агент: Ошибка при обращении к API OpenAI: {e} ---", file=sys.stderr)
        sys.exit(1)

    print("--- Агент: Задача выполнена. Завершение работы. ---", file=sys.stderr)

if __name__ == "__main__":
    main()
