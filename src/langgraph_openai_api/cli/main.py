"""openlang CLI: dev, build, serve commands."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="langgraph-openai-api")
def cli():
    """langgraph-openai-api: Serve LangGraph graphs as OpenAI-compatible APIs."""
    pass


@cli.command()
@click.option("--host", "-h", default="127.0.0.1", help="Bind host")
@click.option("--port", "-p", default=8000, type=int, help="Bind port")
@click.option("--config", "-c", default="./langgraph.json", help="Config file path")
@click.option("--reload/--no-reload", default=True, help="Enable auto-reload")
@click.option("--log-level", default="debug", help="Log level")
def dev(host: str, port: int, config: str, reload: bool, log_level: str):
    """Start development server with hot reload and no auth."""
    config_path = Path(config).resolve()
    if not config_path.exists():
        click.echo(f"Error: Config file not found: {config_path}", err=True)
        sys.exit(2)

    os.environ["OPENLANG_DEV"] = "true"
    os.environ["OPENLANG_CONFIG"] = str(config_path)

    click.echo("openlang dev server starting...")
    click.echo(f"Config: {config_path}")

    try:
        # Validate config loads
        from ..server.app import _load_config
        cfg = _load_config(str(config_path))
        graphs = cfg.get("graphs", {})
        click.echo("Graphs loaded:")
        for gid, mpath in graphs.items():
            click.echo(f"  - {gid:<20} -> {mpath}")
        click.echo()
        click.echo(f"Server: http://{host}:{port}")
        click.echo(f"Docs:   http://{host}:{port}/docs")
        click.echo("Auth:   disabled (dev mode)")
        click.echo()
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(2)

    import uvicorn

    # Create an app factory module reference for uvicorn reload
    os.environ["_OPENLANG_CONFIG_PATH"] = str(config_path)
    os.environ["_OPENLANG_DEV_MODE"] = "true"

    uvicorn.run(
        "langgraph_openai_api.cli._app_factory:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        factory=True,
    )


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", help="Bind host")
@click.option("--port", "-p", default=8000, type=int, help="Bind port")
@click.option("--config", "-c", default="./langgraph.json", help="Config file path")
@click.option("--workers", "-w", default=1, type=int, help="Number of workers")
@click.option("--log-level", default="info", help="Log level")
def serve(host: str, port: int, config: str, workers: int, log_level: str):
    """Start production server with authentication enabled."""
    config_path = Path(config).resolve()
    if not config_path.exists():
        click.echo(f"Error: Config file not found: {config_path}", err=True)
        sys.exit(2)

    api_key = os.environ.get("OPENLANG_API_KEY", "")
    if not api_key:
        click.echo("Error: OPENLANG_API_KEY environment variable is required for serve mode.", err=True)
        sys.exit(4)

    os.environ["OPENLANG_CONFIG"] = str(config_path)

    click.echo("openlang serve starting...")
    click.echo(f"Config: {config_path}")
    click.echo(f"Server: http://{host}:{port}")
    click.echo(f"Workers: {workers}")
    click.echo("Auth:   enabled")
    click.echo()

    import uvicorn

    os.environ["_OPENLANG_CONFIG_PATH"] = str(config_path)
    os.environ["_OPENLANG_DEV_MODE"] = "false"

    uvicorn.run(
        "langgraph_openai_api.cli._app_factory:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        factory=True,
    )


@cli.command()
@click.option("--tag", "-t", default="langgraph-api:latest", help="Image tag")
@click.option("--config", "-c", default="./langgraph.json", help="Config file path")
@click.option("--platform", default=None, help="Target platform (e.g., linux/amd64)")
@click.option("--no-cache", is_flag=True, default=False, help="Disable build cache")
def build(tag: str, config: str, platform: str | None, no_cache: bool):
    """Build a Docker image for deployment."""
    config_path = Path(config).resolve()
    if not config_path.exists():
        click.echo(f"Error: Config file not found: {config_path}", err=True)
        sys.exit(2)

    dockerfile_content = textwrap.dedent("""\
        FROM python:3.11-slim

        WORKDIR /app

        # Install dependencies
        COPY pyproject.toml .
        RUN pip install --no-cache-dir .

        # Copy project files
        COPY . .

        # Install langgraph-openai-api
        RUN pip install langgraph-openai-api

        # Run server
        CMD ["openlang", "serve"]
    """)

    dockerfile_path = Path("Dockerfile.openlang")
    dockerfile_path.write_text(dockerfile_content)
    click.echo(f"Generated Dockerfile: {dockerfile_path}")

    cmd = ["docker", "build", "-f", str(dockerfile_path), "-t", tag]
    if platform:
        cmd.extend(["--platform", platform])
    if no_cache:
        cmd.append("--no-cache")
    cmd.append(".")

    click.echo(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    # Clean up generated Dockerfile
    dockerfile_path.unlink(missing_ok=True)

    if result.returncode != 0:
        click.echo("Docker build failed.", err=True)
        sys.exit(1)

    click.echo(f"Image built successfully: {tag}")


if __name__ == "__main__":
    cli()
