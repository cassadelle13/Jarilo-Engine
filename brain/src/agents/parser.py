import re
from typing import List, Tuple


def parse_code_blocks(text: str) -> List[Tuple[str, str]]:
    """
    Парсит markdown блоки кода из текста.
    
    Адаптировано из open-interpreter (https://github.com/OpenInterpreter/open-interpreter).
    Использует логику парсинга из run_text_llm.py для извлечения блоков кода.

    Args:
        text: The text containing markdown code blocks.

    Returns:
        List of tuples (language, code) for each code block found.
    """
    # Regex to match ```language\ncode\n```
    pattern = r"```(\w*)\n([\s\S]*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    code_blocks = []
    for language, code in matches:
        # If no language specified, default to 'python'
        if not language:
            language = 'python'
        code_blocks.append((language, code.strip()))

    return code_blocks