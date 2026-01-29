"""
Command Line Interface for Jarilo Brain.

Provides convenient commands for development and deployment.
Adapted from MemGPT's CLI structure, now using Typer.
"""

import os
import sys
from pathlib import Path

import typer
import uvicorn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

app = typer.Typer()


@app.command()
def server(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server to"),
    port: int = typer.Option(8000, help="Port to bind the server to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
    log_level: str = typer.Option("info", help="Logging level"),
    workers: int = typer.Option(1, help="Number of worker processes"),
):
    """
    Start the Jarilo Brain server.

    This command starts the FastAPI server with proper configuration
    for development or production use.
    """
    typer.echo(f"Starting Jarilo Brain server on {host}:{port}")

    # Set PYTHONPATH for proper imports
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent)

    import subprocess
    cmd = ["uvicorn", "app:app", "--host", host, "--port", str(port), "--log-level", log_level]
    if reload:
        cmd.append("--reload")
    if workers > 1:
        cmd.extend(["--workers", str(workers)])
    cmd.append("--access-log")

    subprocess.run(cmd, env=env)


@app.command()
def health(url: str = typer.Argument("http://localhost:8000", help="Server URL to check")):
    """
    Check server health status.

    Makes a request to the health endpoint to verify server is running.
    """
    import urllib.request
    import json

    try:
        with urllib.request.urlopen(f"{url}/api/v1/health", timeout=10.0) as response:
            data = json.loads(response.read().decode())
            if response.status == 200:
                typer.echo("✅ Server is healthy")
                typer.echo(data)
            else:
                typer.echo(f"❌ Server returned status {response.status}")
                if response.status == 503:
                    typer.echo("Note: 503 usually means server is running but unhealthy")
    except urllib.error.URLError as e:
        typer.echo(f"❌ Could not connect to server: {e}")
    except Exception as e:
        typer.echo(f"❌ Could not connect to server: {e}")


@app.command()
def init_db():
    """
    Initialize the database.

    Creates all tables and applies migrations.
    """
    from src.orm.db import DatabaseManager

    typer.echo("Initializing database...")

    try:
        db_manager = DatabaseManager()
        import asyncio
        asyncio.run(db_manager.init_db())
        typer.echo("✅ Database initialized successfully")
    except Exception as e:
        typer.echo(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()