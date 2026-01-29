"""
Executor for code execution in isolated environment.
Adapted from Open Interpreter's terminal execution logic.
"""

import subprocess
import sys
import os
import re


def parse_markdown_codeblocks(text: str) -> list:
    """
    Parse markdown code blocks from text.

    Args:
        text: The text containing markdown code blocks

    Returns:
        list: List of dicts with 'language' and 'code' keys
    """
    # Regex to match ```language\ncode\n``` with flexible whitespace
    pattern = r'```\s*(\w+)?\s*\n(.*?)\n\s*```'
    matches = re.findall(pattern, text, re.DOTALL)

    code_blocks = []
    for language, code in matches:
        if not language:
            language = 'bash'  # Default to bash if no language specified
        code_blocks.append({
            'language': language.lower(),
            'code': code.strip()
        })

    return code_blocks


def execute_code(code: str, language: str) -> str:
    """
    Execute code in the specified language.

    Args:
        code: The code to execute
        language: The programming language ('python', 'bash', 'shell', etc.)

    Returns:
        str: The output of the execution
    """
    try:
        if language.lower() in ['python', 'py']:
            # Execute Python code
            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                cwd='/workspace',
                timeout=30
            )
        elif language.lower() in ['bash', 'shell', 'sh']:
            # Execute shell commands
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                cwd='/workspace',
                timeout=30
            )
        else:
            return f"Unsupported language: {language}"

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr

        # Add exit code if non-zero
        if result.returncode != 0:
            output += f"\nExit code: {result.returncode}"

        return output.strip()

    except subprocess.TimeoutExpired:
        return "Execution timed out after 30 seconds"
    except Exception as e:
        return f"Execution error: {str(e)}"