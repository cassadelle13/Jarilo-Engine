#!/bin/bash

# Get tool name and args from environment variables
TOOL_NAME="${TOOL_NAME:-}"
TOOL_ARGS="${TOOL_ARGS:-}"

echo "Plugin Handler: Tool=$TOOL_NAME, Args=$TOOL_ARGS"

case "$TOOL_NAME" in
    "create_app")
        # Parse args: app_name template
        APP_NAME=$(echo "$TOOL_ARGS" | cut -d' ' -f1)
        TEMPLATE=$(echo "$TOOL_ARGS" | cut -d' ' -f2)

        if [ -z "$APP_NAME" ]; then
            echo "Error: APP_NAME is required"
            exit 1
        fi

        TEMPLATE_ARG=""
        if [ -n "$TEMPLATE" ]; then
            TEMPLATE_ARG="-- --template $TEMPLATE"
        fi

        echo "Creating Vite app: $APP_NAME with template: ${TEMPLATE:-default}"
        npm create vite@latest "$APP_NAME" $TEMPLATE_ARG
        ;;
    "install_dependencies")
        # Parse args: app_name
        APP_NAME=$(echo "$TOOL_ARGS" | cut -d' ' -f1)

        if [ -z "$APP_NAME" ]; then
            echo "Error: APP_NAME is required"
            exit 1
        fi

        if [ ! -d "$APP_NAME" ]; then
            echo "Error: Directory $APP_NAME does not exist"
            exit 1
        fi

        echo "Installing dependencies for: $APP_NAME"
        cd "$APP_NAME"
        npm install
        ;;
    *)
        echo "Error: Unknown tool $TOOL_NAME"
        echo "Available tools: create_app, install_dependencies"
        exit 1
        ;;
esac