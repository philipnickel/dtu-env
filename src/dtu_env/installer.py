"""Install conda environments for DTU courses."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from rich.console import Console

from dtu_env.config import GITHUB_RAW_URL
from dtu_env.models import CourseEnvironment
from dtu_env.utils import find_conda_executable

console = Console()


def install_environment(env: CourseEnvironment) -> bool:
    """install a course environment using mamba/conda"""
    exe = find_conda_executable()
    if not exe:
        console.print(
            "[red]Error:[/red] No conda or mamba executable found. "
            "Is Miniforge3 installed and on your PATH?"
        )
        return False

    exe_name = Path(exe).stem
    url = f"{GITHUB_RAW_URL}/{env.filename}"

    console.print(f"\nInstalling [bold cyan]{env.name}[/bold cyan] "
                  f"({env.course_full_name})...")
    console.print(f"Using: [dim]{exe_name}[/dim]")
    console.print(f"Source: [dim]{url}[/dim]\n")

    # Download the YAML to a temp file so conda can read it
    import requests
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, prefix=f"dtu-env-{env.name}-"
    ) as f:
        f.write(response.text)
        tmp_path = f.name

    try:
        cmd = [exe, "env", "create", "-f", tmp_path, "--yes"]
        console.print(f"Running: [dim]{' '.join(cmd)}[/dim]\n")

        result = subprocess.run(
            cmd,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            console.print(
                f"\n[green]Success![/green] Environment [bold]{env.name}[/bold] installed."
            )
            console.print(f"Activate it with: [bold cyan]conda activate {env.name}[/bold cyan]")
            return True
        else:
            console.print(f"\n[red]Error:[/red] Environment creation failed (exit code {result.returncode}).")
            return False
    finally:
        Path(tmp_path).unlink(missing_ok=True)
