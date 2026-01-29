import os
import logging
import subprocess
from openai import OpenAI
from tools.executor import parse_markdown_codeblocks, execute_code

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    logger.info("Jarilo Agent: Запуск агента")
    
    # Получение данных из окружения
    api_key = os.getenv("OPENAI_API_KEY")
    task_prompt = os.getenv("PROMPT")  # Используем PROMPT как в AgentManager
    
    logger.info(f"Jarilo Agent: API_KEY присутствует: {bool(api_key)}")
    logger.info(f"Jarilo Agent: PROMPT присутствует: {bool(task_prompt)}")

    # Проверка наличия данных
    if not api_key:
        logger.error("Jarilo Agent: OPENAI_API_KEY не установлена в переменных окружения.")
        print("Ошибка: OPENAI_API_KEY не установлена в переменных окружения.")
        return

    if not task_prompt:
        logger.error("Jarilo Agent: PROMPT не установлен в переменных окружения.")
        print("Ошибка: PROMPT не установлен в переменных окружения.")
        return

    # Инициализация клиента
    logger.info("Jarilo Agent: Инициализация OpenAI клиента")
    client = OpenAI(api_key=api_key)

    try:
        # System prompt для агента
        system_prompt = """Ты — ИИ-агент, работающий в изолированной среде Linux в директории /workspace.
Для выполнения любых действий (создание файлов, установка зависимостей, запуск скриптов) ты должен генерировать код в markdown-блоках.
Пример для создания файла: 
```bash
echo 'Hello, World!' > /workspace/hello.txt
```
Твоя задача — выполнить шаг плана, который тебе передали, используя эти инструменты. В конце верни краткий отчет о проделанной работе."""

        logger.info(f"Jarilo Agent: Отправка запроса в OpenAI: {task_prompt[:50]}...")
        
        # Вызов LLM
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_prompt}
            ]
        )

        # Извлечение результата
        llm_response = completion.choices[0].message.content
        logger.info(f"Jarilo Agent: Получен ответ от LLM длиной {len(llm_response)} символов")
        
        # Парсинг блоков кода из ответа
        code_blocks = parse_markdown_codeblocks(llm_response)
        logger.info(f"Jarilo Agent: Найдено {len(code_blocks)} блоков кода")
        
        results = []
        
        # Выполнение каждого блока кода
        for i, block in enumerate(code_blocks, 1):
            language = block['language']
            code = block['code']
            logger.info(f"Jarilo Agent: Выполнение блока {i}: {language} ({len(code)} символов)")
            
            # Выполнение кода
            output = execute_code(code, language)
            results.append(f"Блок {i} ({language}):\n{output}")
            logger.info(f"Jarilo Agent: Блок {i} выполнен, результат: {len(output)} символов")
        
        # Сбор финального результата
        if results:
            final_result = "\n\n".join(results)
        else:
            final_result = "Код не найден в ответе LLM или не выполнен."
        
        # Добавление отчета о содержимом /workspace
        ls_result = subprocess.run("ls -la /workspace", shell=True, capture_output=True, text=True)
        ls_output = ls_result.stdout.strip()
        final_result += f"\n\nСодержимое /workspace:\n{ls_output}"
        
        print(final_result)

    except Exception as e:
        logger.error(f"Jarilo Agent: Ошибка: {str(e)}")
        print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    main()