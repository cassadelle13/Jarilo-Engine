# Jarilo System Components Analysis

## Overview
Jarilo is a hybrid intelligence system implementing a multi-agent architecture with task planning, execution, and state management. The system consists of several interconnected components working together to process user prompts and execute code in isolated environments.

## Core Subsystems

### 1. API Endpoints (`brain/src/api/v1/endpoints.py`)
- **Purpose**: REST API interface for task creation and status retrieval
- **Technology**: FastAPI with Pydantic models
- **Key Features**:
  - POST `/tasks/` - Creates and executes tasks
  - GET `/tasks/{task_id}` - Retrieves task status
  - Dependency injection for services
- **Architecture**: Request validation, orchestration of planning and execution phases

### 2. State Management (`brain/src/workspace/state_manager.py`)
- **Purpose**: Persistent storage and retrieval of task states
- **Technology**: TinyDB (JSON-based document database)
- **Key Features**:
  - Task creation with UUID generation
  - Status updates (created, planning, executing, completed, failed)
  - Plan storage and result tracking
  - Async operations with thread pools
- **Architecture**: CRUD operations with type normalization

### 3. Task Planner (`brain/src/orchestration/planner.py`)
- **Purpose**: Converts natural language prompts into executable code plans
- **Technology**: OpenAI GPT models with custom prompting
- **Key Features**:
  - LLM-based task decomposition
  - Fallback logic for simple commands
  - Markdown code block generation
  - Error handling with custom exceptions
- **Architecture**: Function calling simulation, atomic step generation

### 4. Task Executor (`brain/src/orchestration/executor.py`)
- **Purpose**: Orchestrates execution of planned tasks via external agents
- **Technology**: HTTP client communication with agent services
- **Key Features**:
  - Agent communication via REST API
  - Result processing and state updates
  - Error propagation
- **Architecture**: Delegation pattern to isolated execution environments

### 5. Error Handling (`brain/src/main.py`, `brain/src/utils/watcher.py`)
- **Purpose**: Centralized exception management and logging
- **Technology**: FastAPI exception handlers + custom middleware
- **Key Features**:
  - Global exception handler returning JSON 500 responses
  - Structured logging with context
  - Graceful error propagation
- **Architecture**: Framework-level exception interception

### 6. Agent System (`agents/jarilo-agent/`)
- **Purpose**: Isolated code execution environment
- **Technology**: Docker container with mistune markdown parser
- **Key Features**:
  - Markdown parsing for code block extraction
  - Sequential bash/python execution
  - Sandboxed environment with workspace
- **Architecture**: HTML generation from markdown, regex-based code extraction

### 7. Configuration and Dependencies (`brain/src/api/dependencies.py`)
- **Purpose**: Service instantiation and dependency injection
- **Technology**: FastAPI dependency system
- **Key Features**:
  - Singleton service management
  - Async initialization
  - Logging configuration
- **Architecture**: DI container pattern

### 8. Data Models (`brain/src/api/v1/schemas.py`)
- **Purpose**: API request/response validation
- **Technology**: Pydantic models
- **Key Features**:
  - Input validation
  - Response serialization
  - Type safety
- **Architecture**: Schema-driven development

## System Architecture
- **Frontend**: REST API with JSON communication
- **Backend**: Async Python services with external LLM integration
- **Storage**: File-based JSON database
- **Execution**: Containerized agent with code parsing
- **Communication**: HTTP between brain and agent services

## Key Design Patterns
- Dependency Injection
- Repository pattern (StateManager)
- Strategy pattern (Planner with fallbacks)
- Observer pattern (State updates)
- Adapter pattern (Agent communication)