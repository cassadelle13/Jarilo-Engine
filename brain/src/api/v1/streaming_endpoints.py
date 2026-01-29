from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from workspace.state_manager import StateManager
from orchestration.simple_integrated_graph import get_simple_integrated_orchestrator
from api.dependencies import get_state_manager, get_llm
from .schemas import TaskCreate, Task
import logging
from core.logging import LogContext

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_supported_types():
    return {
        "trigger": {"kind": "trigger"},
        "webhook": {"kind": "trigger"},
        "schedule": {"kind": "trigger"},
        "manual": {"kind": "trigger"},
        "http": {"kind": "tool", "tool": "web", "actions": ["get", "post"]},
        "api": {"kind": "tool", "tool": "web", "actions": ["get", "post"]},
        "http_auth": {"kind": "tool", "tool": "auth_http", "actions": ["request"]},
        "database": {"kind": "tool", "tool": "db", "actions": ["query"]},
        "file": {
            "kind": "tool",
            "tool": "file_tool",
            "actions": ["read", "write", "append", "list", "mkdir"],
        },
        "script": {"kind": "tool", "tool": "shell", "actions": ["execute"]},
    }


def _get_node_type(node: dict) -> str:
    return (node.get("data") or {}).get("type")


def _toposort_or_raise(nodes: list[dict], edges: list[dict]) -> list[str]:
    node_ids = [n.get("id") for n in nodes]
    if any(not nid for nid in node_ids):
        raise HTTPException(status_code=400, detail="All nodes must have non-empty 'id'")
    node_id_set = set(node_ids)
    if len(node_id_set) != len(node_ids):
        raise HTTPException(status_code=400, detail="Duplicate node ids detected")

    outgoing: dict[str, set[str]] = {nid: set() for nid in node_id_set}
    indegree: dict[str, int] = {nid: 0 for nid in node_id_set}

    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        if not src or not tgt:
            raise HTTPException(status_code=400, detail="All edges must have 'source' and 'target'")
        if src not in node_id_set or tgt not in node_id_set:
            raise HTTPException(status_code=400, detail=f"Edge references unknown node: {src} -> {tgt}")
        if tgt not in outgoing[src]:
            outgoing[src].add(tgt)
            indegree[tgt] += 1

    # Kahn's algorithm
    queue = [nid for nid, deg in indegree.items() if deg == 0]
    order: list[str] = []
    while queue:
        nid = queue.pop(0)
        order.append(nid)
        for nxt in outgoing[nid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(node_id_set):
        raise HTTPException(status_code=400, detail="Workflow contains a cycle (v0 DAG-only executor)")

    return order

@router.get("/tasks/{task_id}/stream")
async def stream_task_execution(
    task_id: str,
    state_manager: StateManager = Depends(get_state_manager),
    llm = Depends(get_llm)
):
    """
    Stream task execution in real-time using Server-Sent Events.
    
    Provides real-time updates about task progress including:
    - Planning phase
    - Execution steps
    - Tool calls
    - Results
    - Errors
    
    Args:
        task_id: UUID of the task to stream
        state_manager: State manager from DI
        llm: Language model from DI
    
    Returns:
        StreamingResponse: SSE stream with task events
    """
    
    async def generate_events() -> AsyncGenerator[str, None]:
        """Generate SSE events for task execution."""
        
        try:
            # Get task from database
            task = await state_manager.get_task(task_id=task_id)
            if task is None:
                yield f"data: {json.dumps({'event_type': 'ERROR', 'data': {'error': f'Task {task_id} not found'}})}\n\n"
                return
            
            # Send initial event
            yield f"data: {json.dumps({'event_type': 'TASK_STARTED', 'data': {'task_id': task_id, 'prompt': task['prompt']}})}\n\n"
            
            # Set logging context
            LogContext.set("task_id", task_id)
            
            # Get orchestrator
            orchestrator = get_simple_integrated_orchestrator(llm)
            
            # Create custom streaming execution
            async def stream_execution():
                """Stream execution steps."""
                
                # Step 1: Planning
                yield f"data: {json.dumps({'event_type': 'PLANNING_STARTED', 'data': {'phase': 'planning'}})}\n\n"
                
                # Simulate planning delay
                await asyncio.sleep(1)
                
                # Get plan from orchestrator
                plan_result = await orchestrator.execute(task['prompt'])
                
                yield f"data: {json.dumps({'event_type': 'PLANNING_COMPLETED', 'data': {'plan': plan_result.get('plan', [])}})}\n\n"
                
                # Step 2: Execution
                yield f"data: {json.dumps({'event_type': 'EXECUTION_STARTED', 'data': {'phase': 'execution'}})}\n\n"
                
                # Execute each step
                plan = plan_result.get('plan', [])
                for i, step in enumerate(plan):
                    yield f"data: {json.dumps({'event_type': 'STEP_STARTED', 'data': {'step': i+1, 'total': len(plan), 'description': step}})}\n\n"
                    
                    # Simulate step execution
                    await asyncio.sleep(0.5)
                    
                    yield f"data: {json.dumps({'event_type': 'STEP_COMPLETED', 'data': {'step': i+1, 'result': f'Completed: {step}'}})}\n\n"
                
                # Step 3: Completion
                yield f"data: {json.dumps({'event_type': 'TASK_COMPLETED', 'data': {'result': plan_result.get('final_result', [])}})}\n\n"
                
                # Update task in database
                await state_manager.update_task_status(task_id=task_id, new_status="completed")
            
            # Stream execution
            async for event in stream_execution():
                yield event
            
        except Exception as e:
            logger.error(f"Error in stream_task_execution: {e}")
            yield f"data: {json.dumps({'event_type': 'ERROR', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.get("/tools/")
async def get_available_tools():
    """
    Get list of available tools for workflow generation.
    
    Returns:
        List of available tools with their schemas
    """
    try:
        from tools.registry import tool_registry
        
        tools = tool_registry.get_all_tools()
        tool_schemas = []
        
        for tool in tools:
            tool_schemas.append({
                "name": tool.name,
                "description": tool.description,
                "schema": getattr(tool, 'schema', {})
            })
        
        return {
            "tools": tool_schemas,
            "total": len(tool_schemas)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        return {"tools": [], "total": 0, "error": str(e)}


@router.get("/catalog/nodes")
async def get_node_catalog():
    try:
        from tools.registry import tool_registry

        tools = tool_registry.get_all_tools()
        tool_schemas_by_name = {}
        for tool in tools:
            try:
                schema = tool.get_schema()
            except Exception:
                schema = {}
            tool_schemas_by_name[getattr(tool, "name", "")] = schema

        supported_types = _build_supported_types()

        nodes = []
        for node_type, spec in supported_types.items():
            node_entry = {
                "type": node_type,
                "kind": spec["kind"],
                "supported": True,
                "schema": {},
            }

            if spec["kind"] == "tool":
                tool_name = spec["tool"]
                node_entry["tool"] = tool_name
                node_entry["actions"] = spec.get("actions", [])
                node_entry["schema"] = tool_schemas_by_name.get(tool_name, {})

            nodes.append(node_entry)

        return {
            "nodes": nodes,
            "total": len(nodes),
        }
    except Exception as e:
        logger.error(f"Error getting node catalog: {e}")
        return {"nodes": [], "total": 0, "error": str(e)}


@router.post("/workflows/run")
async def run_workflow(workflow_data: dict):
    """Compile and execute UI workflow.

    v0 constraints:
    - DAG only (no cycles)
    - linear execution following topological order
    - parameters are read from node.data as flat fields
    """
    from tools.registry import tool_registry

    if isinstance(workflow_data, dict) and isinstance(workflow_data.get("workflow"), dict):
        workflow_data = workflow_data["workflow"]

    nodes = workflow_data.get("nodes", [])
    edges = workflow_data.get("edges", [])

    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise HTTPException(status_code=400, detail="workflow_data.nodes and workflow_data.edges must be arrays")

    supported_types = _build_supported_types()
    trigger_types = {"trigger", "webhook", "schedule", "manual"}

    # Build node lookup
    node_by_id: dict[str, dict] = {}
    for n in nodes:
        nid = n.get("id")
        if not nid:
            raise HTTPException(status_code=400, detail="Each node must have an 'id'")
        node_by_id[nid] = n

    # Validate node types
    unknown_types = []
    for n in nodes:
        ntype = _get_node_type(n)
        if not ntype:
            unknown_types.append({"id": n.get("id"), "type": None})
            continue
        if ntype not in supported_types:
            unknown_types.append({"id": n.get("id"), "type": ntype})

    if unknown_types:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Unsupported node types",
                "unsupported": unknown_types,
                "supported": sorted(list(supported_types.keys())),
            },
        )

    # Validate trigger
    has_trigger = any(_get_node_type(n) in trigger_types for n in nodes)
    if not has_trigger:
        raise HTTPException(status_code=400, detail="Workflow must contain at least one trigger node")

    # Compile order
    execution_order = _toposort_or_raise(nodes, edges)

    results: dict[str, dict] = {}
    execution_trace: list[dict] = []

    # Execute
    for nid in execution_order:
        node = node_by_id[nid]
        data = node.get("data") or {}
        ntype = data.get("type")
        spec = supported_types[ntype]

        # Skip triggers in v0 execution (they don't call tools)
        if spec["kind"] == "trigger":
            execution_trace.append({"node_id": nid, "type": ntype, "status": "skipped", "reason": "trigger"})
            results[nid] = {"status": "skipped", "type": ntype}
            continue

        tool_name = spec["tool"]
        actions = spec.get("actions", [])

        # Map node.data -> tool call
        try:
            if ntype in ("http", "api"):
                method = str(data.get("method") or "GET").lower()
                if method not in actions:
                    raise HTTPException(status_code=400, detail=f"Unsupported HTTP method for {ntype}: {method}")
                url = data.get("url")
                if not url:
                    raise HTTPException(status_code=400, detail=f"Node {nid} missing required field data.url")

                body = data.get("body")
                # If body is a string (NodeEditor http uses textarea), try parse JSON; otherwise pass as-is
                payload = None
                if body not in (None, ""):
                    if isinstance(body, str):
                        try:
                            payload = json.loads(body)
                        except Exception:
                            payload = body
                    else:
                        payload = body

                tool_result = await tool_registry.execute_tool(f"web.{method}", url=url, data=payload or {})

            elif ntype == "http_auth":
                url = data.get("url")
                if not url:
                    raise HTTPException(status_code=400, detail=f"Node {nid} missing required field data.url")

                method = str(data.get("method") or "GET").lower()
                if method not in {"get", "post"}:
                    raise HTTPException(status_code=400, detail=f"Unsupported HTTP method for {ntype}: {method}")

                auth = data.get("auth")
                if not isinstance(auth, dict):
                    raise HTTPException(status_code=400, detail=f"Node {nid} missing required field data.auth")

                body = data.get("body")
                if body is None and "data" in data:
                    body = data.get("data")

                payload = None
                if body not in (None, ""):
                    if isinstance(body, str):
                        try:
                            payload = json.loads(body)
                        except Exception:
                            payload = body
                    else:
                        payload = body

                headers = data.get("headers")
                if headers is None:
                    headers = {}

                tool_result = await tool_registry.execute_tool(
                    "auth_http.request",
                    url=url,
                    method=method,
                    body=payload,
                    headers=headers,
                    auth=auth,
                )

            elif ntype == "database":
                query = data.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail=f"Node {nid} missing required field data.query")
                tool_result = await tool_registry.execute_tool("db.query", query=query)

            elif ntype == "file":
                # NodeEditor uses fileName; backend tool uses path
                op = str(data.get("operation") or "read").lower()
                if op == "convert" or op == "extract":
                    raise HTTPException(status_code=400, detail=f"File operation not supported in backend v0: {op}")
                if op not in actions:
                    raise HTTPException(status_code=400, detail=f"Unsupported file operation: {op}")

                path = data.get("path") or data.get("fileName")
                if not path:
                    raise HTTPException(status_code=400, detail=f"Node {nid} missing required field data.fileName (or data.path)")

                content = data.get("content")
                tool_result = await tool_registry.execute_tool(f"file.{op}", path=path, content=content or "")

            elif ntype == "script":
                # NodeEditor uses jsCode/pythonCode; backend tool expects command string.
                # v0: execute raw command from data.command, else fallback to data.code
                command = data.get("command") or data.get("code")
                if not command:
                    raise HTTPException(status_code=400, detail=f"Node {nid} missing required field data.command (or data.code)")
                tool_result = await tool_registry.execute_tool("shell.execute", command=command)
            else:
                raise HTTPException(status_code=400, detail=f"Execution not implemented for node type: {ntype}")

            results[nid] = {
                "status": "completed" if tool_result.get("success") else "failed",
                "type": ntype,
                "tool": tool_result.get("tool"),
                "action": tool_result.get("action"),
                "output": tool_result.get("output"),
                "error": tool_result.get("error"),
            }
            execution_trace.append({"node_id": nid, "type": ntype, "status": results[nid]["status"]})

            if not tool_result.get("success"):
                # Stop on first failure in v0
                break

        except HTTPException:
            raise
        except Exception as e:
            results[nid] = {"status": "failed", "type": ntype, "error": str(e)}
            execution_trace.append({"node_id": nid, "type": ntype, "status": "failed", "error": str(e)})
            break

    return {
        "ok": all(r.get("status") in ("completed", "skipped") for r in results.values()),
        "execution_order": execution_order,
        "results": results,
        "trace": execution_trace,
    }

@router.post("/workflows/validate")
async def validate_workflow(workflow_data: dict):
    """
    Validate workflow structure and provide suggestions.
    
    Args:
        workflow_data: Workflow with nodes and edges
    
    Returns:
        Validation result with errors and suggestions
    """
    try:
        if isinstance(workflow_data, dict) and isinstance(workflow_data.get("workflow"), dict):
            workflow_data = workflow_data["workflow"]

        nodes = workflow_data.get('nodes', [])
        edges = workflow_data.get('edges', [])

        errors = []
        suggestions = []

        if not isinstance(nodes, list) or not isinstance(edges, list):
            return {
                "is_valid": False,
                "errors": ["workflow_data.nodes and workflow_data.edges must be arrays"],
                "suggestions": [],
                "metrics": {},
            }

        supported_types = _build_supported_types()
        trigger_types = {"trigger", "webhook", "schedule", "manual"}

        node_by_id = {}
        for node in nodes:
            nid = node.get('id')
            if not nid:
                errors.append("Each node must have an 'id'")
                continue
            if nid in node_by_id:
                errors.append(f"Duplicate node id: {nid}")
                continue
            node_by_id[nid] = node

        for edge in edges:
            src = edge.get('source')
            tgt = edge.get('target')
            if not src or not tgt:
                errors.append("Each edge must have 'source' and 'target'")
                continue
            if src not in node_by_id or tgt not in node_by_id:
                errors.append(f"Edge references unknown node: {src} -> {tgt}")

        has_trigger = any((node.get('data') or {}).get('type') in trigger_types for node in nodes)
        if not has_trigger:
            errors.append("Workflow should contain at least one trigger node")
            suggestions.append("Add a trigger node to start the workflow")

        for node in nodes:
            nid = node.get('id')
            data = node.get('data') or {}
            ntype = data.get('type')

            if not ntype:
                errors.append(f"Node {nid} is missing data.type")
                continue

            if ntype not in supported_types:
                errors.append(f"Node {nid} has unsupported data.type: {ntype}")
                continue

            if supported_types[ntype]['kind'] == 'trigger':
                continue

            if ntype in {"http", "api"}:
                url = data.get('url')
                method = str(data.get('method') or '').lower()
                if not url:
                    errors.append(f"Node {nid} ({ntype}) missing required field: data.url")
                if not method:
                    errors.append(f"Node {nid} ({ntype}) missing required field: data.method")
                elif method not in {"get", "post"}:
                    errors.append(f"Node {nid} ({ntype}) has unsupported method: {method}")

            elif ntype == "http_auth":
                url = data.get('url')
                method = str(data.get('method') or '').lower()
                auth = data.get('auth')
                if not url:
                    errors.append(f"Node {nid} (http_auth) missing required field: data.url")
                if not method:
                    errors.append(f"Node {nid} (http_auth) missing required field: data.method")
                elif method not in {"get", "post"}:
                    errors.append(f"Node {nid} (http_auth) has unsupported method: {method}")

                if not isinstance(auth, dict):
                    errors.append(f"Node {nid} (http_auth) missing required field: data.auth")
                else:
                    mode = auth.get('mode')
                    cred_ref = auth.get('credential_ref')
                    if not mode:
                        errors.append(f"Node {nid} (http_auth) missing required field: data.auth.mode")
                    elif str(mode).lower() not in {"bearer", "basic", "api_key"}:
                        errors.append(f"Node {nid} (http_auth) has unsupported auth.mode: {mode}")
                    if not cred_ref:
                        errors.append(f"Node {nid} (http_auth) missing required field: data.auth.credential_ref")

            elif ntype == 'database':
                query = data.get('query')
                if not query:
                    errors.append(f"Node {nid} (database) missing required field: data.query")

            elif ntype == 'file':
                op = str(data.get('operation') or 'read').lower()
                if op in {"convert", "extract"}:
                    errors.append(f"Node {nid} (file) operation not supported on backend: {op}")
                elif op not in {"read", "write", "append", "list", "mkdir"}:
                    errors.append(f"Node {nid} (file) has unsupported operation: {op}")

                path = data.get('path') or data.get('fileName')
                if not path:
                    errors.append(f"Node {nid} (file) missing required field: data.fileName (or data.path)")

            elif ntype == 'script':
                command = data.get('command') or data.get('code')
                if not command:
                    errors.append(f"Node {nid} (script) missing required field: data.command (or data.code)")

        connected_nodes = set()
        if nodes:
            for edge in edges:
                if edge.get('source'):
                    connected_nodes.add(edge['source'])
                if edge.get('target'):
                    connected_nodes.add(edge['target'])

            if len(nodes) > 1:
                disconnected = len(nodes) - len(connected_nodes)
                if disconnected > 0:
                    errors.append(f"{disconnected} nodes are not connected")
                    suggestions.append("Connect all nodes to create a valid workflow")

        if nodes and edges:
            try:
                _toposort_or_raise(nodes, edges)
            except HTTPException as he:
                errors.append(str(he.detail))

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "suggestions": suggestions,
            "metrics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "connected_nodes": len(connected_nodes) if nodes else 0,
            }
        }

    except Exception as e:
        logger.error(f"Error validating workflow: {e}")
        return {
            "is_valid": False,
            "errors": [str(e)],
            "suggestions": [],
            "metrics": {},
        }
