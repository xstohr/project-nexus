"""Deployment utilities for Nexus."""

import os
import subprocess
import typer
from typing import Optional, List


def deploy_stack(stack_name: str, region: Optional[str] = None) -> None:
    """Deploy the Nexus SAM application."""
    typer.echo(f"Deploying Nexus SAM application: {stack_name}")
    
    # Get the template file path
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "template.yaml"
    )
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"SAM template not found: {template_path}")
    
    # Change to the project root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Build the SAM application
    typer.echo("Building SAM application...")
    build_result = subprocess.run(["sam", "build"], capture_output=True, text=True)
    
    if build_result.returncode != 0:
        typer.echo(f"Error building SAM application: {build_result.stderr}", err=True)
        raise RuntimeError(f"SAM build failed: {build_result.stderr}")
    
    typer.echo("SAM build completed successfully.")
    
    # Deploy the SAM application
    deploy_cmd: List[str] = ["sam", "deploy"]
    
    # Add optional parameters
    if stack_name:
        deploy_cmd.extend(["--stack-name", stack_name])
    
    if region:
        deploy_cmd.extend(["--region", region])
    
    # Add required capabilities
    deploy_cmd.extend([
        "--capabilities", "CAPABILITY_IAM", "CAPABILITY_NAMED_IAM",
        "--no-fail-on-empty-changeset"
    ])
    
    typer.echo(f"Deploying SAM application with command: {' '.join(deploy_cmd)}")
    deploy_result = subprocess.run(deploy_cmd, capture_output=True, text=True)
    
    if deploy_result.returncode != 0:
        typer.echo(f"Error deploying SAM application: {deploy_result.stderr}", err=True)
        raise RuntimeError(f"SAM deploy failed: {deploy_result.stderr}")
    
    typer.echo("SAM deployment completed successfully.")
    typer.echo(deploy_result.stdout) 