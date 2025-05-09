"""Command-line interface for Nexus."""

import typer
from typing import Optional
import sys

from nexus import __version__

app = typer.Typer()


@app.callback()
def callback() -> None:
    """Nexus - A modern cloud-based application."""
    pass


@app.command()
def version() -> None:
    """Show the version of Nexus."""
    typer.echo(f"Nexus version: {__version__}")


@app.command()
def deploy(
    stack_name: str = typer.Option("nexus", help="CloudFormation stack name"),
    region: Optional[str] = typer.Option(None, help="AWS region to deploy to"),
) -> None:
    """Deploy Nexus to AWS using CloudFormation."""
    from nexus.deployment import deploy_stack
    try:
        deploy_stack(stack_name=stack_name, region=region)
    except Exception as e:
        typer.echo(f"Error deploying Nexus: {e}", err=True)
        sys.exit(1)


@app.command()
def run(
    debug: bool = typer.Option(False, help="Enable debug mode"),
) -> None:
    """Run the Nexus application locally."""
    typer.echo("Starting Nexus application...")
    if debug:
        typer.echo("Debug mode enabled")
    # Implement application run logic here
    typer.echo("Nexus application running. Press Ctrl+C to exit.")


if __name__ == "__main__":
    app() 