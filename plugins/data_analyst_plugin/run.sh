#!/bin/bash
# run.sh для Data Analyst Plugin
# Принимает путь к Python-скрипту через переменную окружения TOOL_ARGS или аргумент командной строки

SCRIPT_PATH="$TOOL_ARGS"

if [ -z "$SCRIPT_PATH" ]; then
    # Fallback to command line argument
    SCRIPT_PATH="$1"
fi

if [ -z "$SCRIPT_PATH" ]; then
    echo "Usage: $0 <python_script_path> or set TOOL_ARGS environment variable"
    exit 1
fi

# If path is not absolute, assume it's in workspace
if [[ "$SCRIPT_PATH" != /* ]]; then
    SCRIPT_PATH="/workspace/$SCRIPT_PATH"
fi

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script file '$SCRIPT_PATH' not found"
    exit 1
fi

echo "Executing Python script: $SCRIPT_PATH"
python3 "$SCRIPT_PATH"