#!/bin/bash
echo "Jarilo Agent: Запуск агента"
PROMPT="$PROMPT"
echo "Jarilo Agent: Получен промпт: $PROMPT"

# Use Python to extract and execute code blocks
cd /workspace
python3 - << 'EOF'
import os
import sys
import mistune
import re
import html

prompt = os.environ.get('PROMPT', '')
print(f"Mistune parser: Processing prompt: {prompt[:100]}...")

# Use mistune to parse markdown to HTML
html_content = mistune.markdown(prompt)
print(f"Mistune parser: Generated HTML: {html_content[:200]}...")

# Extract code blocks from HTML
code_blocks = re.findall(r'<pre><code class="language-(\w+)">(.*?)</code></pre>', html_content, re.DOTALL)

print(f"Mistune parser: Found {len(code_blocks)} code blocks")

if code_blocks:
    for lang, code in code_blocks:
        # Unescape HTML entities
        code = html.unescape(code)
        print(f"Mistune parser: Found {lang} code block")
        print(f"Code: {code[:100]}...")
        
        if lang in ['bash', 'sh']:
            print("Mistune parser: Executing bash code")
            # Write code to temp file and execute
            with open('/tmp/temp_script.sh', 'w') as f:
                f.write('#!/bin/bash\n')
                f.write(code)
            os.chmod('/tmp/temp_script.sh', 0o755)
            result = os.system('/tmp/temp_script.sh')
            print(f"Bash execution result: {result}")
        elif lang == 'python':
            print("Mistune parser: Executing python code")
            result = os.system(f'python3 -c "{code.replace(chr(34), chr(92)+chr(34))}"')
            print(f"Python execution result: {result}")
else:
    print("Mistune parser: No code blocks found, creating default file")
    with open('/workspace/hello.txt', 'w') as f:
        f.write("Hello, Genesis!")

print("Mistune parser: Done")
EOF

echo "Jarilo Agent: Выполнение завершено"