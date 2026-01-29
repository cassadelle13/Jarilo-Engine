"""
Plugin Sandbox - Local Docker container management for plugins.
Inspired by E2B's sandbox architecture but using docker-py for local execution.
"""

import asyncio
import logging
import os
from typing import Optional, AsyncGenerator, Tuple
import docker
from docker.models.containers import Container
from docker.errors import DockerException

logger = logging.getLogger(__name__)


class PluginSandbox:
    """
    Manages a Docker container for plugin execution.
    Provides high-level interface for starting, executing commands, and stopping containers.
    """

    def __init__(self, plugin_path: str, workspace_path: str = "/workspace", image_name: str = None):
        """
        Initialize the sandbox.

        :param plugin_path: Path to the plugin directory containing Dockerfile
        :param workspace_path: Path inside container where workspace is mounted
        :param image_name: Name/tag for the Docker image
        """
        self.plugin_path = plugin_path
        self.workspace_path = workspace_path
        self.image_name = image_name
        self.container: Optional[Container] = None
        self.client = docker.from_env()

    async def start(self) -> None:
        """
        Build and start the container from the plugin's Dockerfile.
        Mounts the current working directory as workspace.
        """
        try:
            if self.image_name:
                logger.info(f"Using existing image: {self.image_name}")
                image = self.client.images.get(self.image_name)
            else:
                logger.info(f"Building container for plugin: {self.plugin_path}")

                # Build the image
                image, build_logs = await asyncio.to_thread(
                    self.client.images.build,
                    path=self.plugin_path,
                    tag=f"jarilo-plugin-{os.path.basename(self.plugin_path)}",
                    rm=True
                )

                # Log build output
                for log in build_logs:
                    if 'stream' in log:
                        logger.debug(f"Build: {log['stream'].strip()}")

            logger.info(f"Starting container from image: {image.id}")

            # Start the container
            # Mount current directory as workspace
            volumes = {
                os.getcwd(): {
                    'bind': self.workspace_path,
                    'mode': 'rw'
                }
            }

            self.container = await asyncio.to_thread(
                self.client.containers.run,
                image.id,
                detach=True,
                volumes=volumes,
                working_dir=self.workspace_path,
                environment={
                    'WORKSPACE': self.workspace_path
                }
            )

            logger.info(f"Container started: {self.container.id}")

        except DockerException as e:
            logger.error(f"Failed to start container: {e}")
            raise

    async def execute(self, command: str, env_vars: dict = None) -> AsyncGenerator[str, None]:
        """
        Execute a command in the running container and stream output.

        :param command: Command to execute
        :param env_vars: Environment variables to set
        :yield: Output lines from stdout/stderr
        """
        if not self.container:
            raise RuntimeError("Container not started. Call start() first.")

        # Check if container is running
        self.container.reload()
        if self.container.status != 'running':
            raise RuntimeError(f"Container is not running. Status: {self.container.status}")

        try:
            logger.info(f"Executing command in container: {command}")
            if env_vars:
                logger.info(f"With env vars: {env_vars}")

            # Run the command
            exec_result = await asyncio.to_thread(
                self.container.exec_run,
                command,
                environment=env_vars
            )

            logger.info(f"exec_result type: {type(exec_result)}")
            logger.info(f"exec_result keys: {exec_result.keys() if isinstance(exec_result, dict) else 'not dict'}")
            logger.info(f"exec_result: {exec_result}")

            # Get output
            if exec_result and 'output' in exec_result:
                output = exec_result['output']
                if isinstance(output, bytes):
                    output = output.decode('utf-8')
                for line in output.splitlines():
                    if line.strip():
                        logger.debug(f"Output: {line}")
                        yield line

        except DockerException as e:
            logger.error(f"Failed to execute command: {e}")
            raise

    async def stop(self) -> None:
        """
        Stop and remove the container.
        """
        if self.container:
            try:
                logger.info(f"Stopping container: {self.container.id}")
                await asyncio.to_thread(
                    self.container.stop,
                    timeout=10
                )

                logger.info(f"Removing container: {self.container.id}")
                await asyncio.to_thread(
                    self.container.remove
                )

                self.container = None
                logger.info("Container stopped and removed")

            except DockerException as e:
                logger.error(f"Failed to stop container: {e}")
                raise

    async def is_running(self) -> bool:
        """
        Check if the container is running.
        """
        if not self.container:
            return False

        try:
            self.container.reload()
            return self.container.status == 'running'
        except DockerException:
            return False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()