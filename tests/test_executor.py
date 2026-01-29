import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent', 'src'))
from tools.executor import parse_markdown_codeblocks

# Тест парсинга
test_md = """```bash
echo 'Hello, World!' > /workspace/hello.txt
```"""

print("Тестовая строка:")
print(repr(test_md))
blocks = parse_markdown_codeblocks(test_md)
print("Парсинг результата:", blocks)

# Тест выполнения
if blocks:
    from tools.executor import execute_code
    result = execute_code(blocks[0]['code'], blocks[0]['language'])
    print("Результат выполнения:", result)