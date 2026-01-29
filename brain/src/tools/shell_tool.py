"""
ShellTool for executing shell commands asynchronously with sandboxing.
Adapted from Open-Interpreter's subprocess architecture and enhanced with Docker sandboxing.
"""

import asyncio
import os
import platform
import tempfile
import docker
from typing import Optional
import logging

from .base import BaseTool, ToolResult


class ShellTool(BaseTool):
    """Tool for executing shell commands with streaming output and sandboxing."""

    name = "shell"
    description = "Execute shell commands and capture stdout/stderr output in real-time with sandboxing"

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            self.logger.warning(f"Docker not available, falling back to direct execution: {e}")
            self.docker_client = None

    def get_schema(self):
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"]
            }
        }

    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Execute shell command with sandboxing."""
        if action != "execute":
            return ToolResult(error=f"Unknown action: {action}")

        command = kwargs.get("command")
        if not command:
            return ToolResult(error="Command is required")

        try:
            self.logger.info(f"Executing shell command with sandboxing: {command}")

            if self.docker_client:
                result = await self._run_in_docker_sandbox(command)
            else:
                result = await self._run_direct(command)

            return result
        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
            return ToolResult(error=str(e))

    async def _run_in_docker_sandbox(self, command: str) -> ToolResult:
        """Run command in Docker sandbox for isolation."""
        try:
            # Create a temporary script to execute
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write("#!/bin/bash\n")
                f.write(f"{command}\n")
                script_path = f.name

            # Make script executable
            os.chmod(script_path, 0o755)

            # Run in Docker container
            container = self.docker_client.containers.run(
                "alpine:latest",  # Lightweight sandbox
                command=["/bin/sh", "/tmp/script.sh"],
                volumes={script_path: {"bind": "/tmp/script.sh", "mode": "ro"}},
                working_dir="/tmp",
                detach=False,
                stdout=True,
                stderr=True,
                remove=True,  # Auto-remove container
                mem_limit="128m",  # Memory limit
                cpu_quota=50000,  # CPU limit (0.5 cores)
                read_only=True,  # Read-only filesystem
                tmpfs={"/tmp": ""},  # Temporary writable directory
                network_mode="none",  # No network access
                user="1000:1000"  # Non-root user
            )

            # Container.run with detach=False returns the output directly
            output = container.decode('utf-8', errors='replace')

            # Clean up
            os.unlink(script_path)

            return ToolResult(output=output)

        except docker.errors.ContainerError as e:
            return ToolResult(error=f"Container error: {e.stderr.decode('utf-8', errors='replace')}")
        except Exception as e:
            return ToolResult(error=f"Docker sandbox failed: {str(e)}")

    async def _run_direct(self, command: str) -> ToolResult:
        """Fallback: run command directly (less secure)."""
        self.logger.warning("Using direct command execution (not sandboxed)")

        # Start the subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()  # Use current working directory
        )

        # Collect output from both streams
        stdout_lines = []
        stderr_lines = []

        # Read stdout and stderr concurrently
        async def read_stream(stream, lines_list, stream_name):
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    line = line.decode('utf-8', errors='replace').rstrip('\n\r')
                    if line:  # Only add non-empty lines
                        lines_list.append(line)
                        self.logger.debug(f"{stream_name}: {line}")
            except Exception as e:
                self.logger.error(f"Error reading {stream_name}: {e}")

        # Create tasks for reading both streams
        stdout_task = asyncio.create_task(read_stream(process.stdout, stdout_lines, "stdout"))
        stderr_task = asyncio.create_task(read_stream(process.stderr, stderr_lines, "stderr"))

        # Wait for both tasks to complete
        await asyncio.gather(stdout_task, stderr_task)

        # Wait for process to finish
        return_code = await process.wait()

        # Combine output
        combined_output = []
        if stdout_lines:
            combined_output.append("STDOUT:")
            combined_output.extend(stdout_lines)
        if stderr_lines:
            if combined_output:
                combined_output.append("")
            combined_output.append("STDERR:")
            combined_output.extend(stderr_lines)

        output = "\n".join(combined_output) if combined_output else ""

        if return_code != 0:
            error_msg = f"Command failed with return code {return_code}"
            if stderr_lines:
                error_msg += f"\nSTDERR: {' '.join(stderr_lines)}"
            return ToolResult(output=output, error=error_msg)

        return ToolResult(output=output)