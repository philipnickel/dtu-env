"""Install conda environments for DTU courses."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from importlib.resources import files
from pathlib import Path

from rich.console import Console

from dtu_env.api import CourseEnvironment


console = Console()


def _find_conda_executable() -> str:
    """find mamba or conda executable, preferring mamba"""
    for name in ("mamba", "conda"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError(
        "No conda or mamba executable found. "
        "Is Miniforge3 installed and on your PATH?"
    )


def install_environment(env: CourseEnvironment) -> None:
    """install a course environment using mamba/conda"""
    exe = _find_conda_executable()

    console.print(f"\nInstalling [bold cyan]{env.name}[/bold cyan] "
                  f"({env.course_full_name})...")
    console.print(f"Using: [dim]{Path(exe).stem}[/dim]")

    # Read bundled YAML file
    yaml_path = files("dtu_env").joinpath("environments").joinpath(env.filename)
    yaml_content = yaml_path.read_text()

    # Write to temp file for conda to read
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, prefix=f"dtu-env-{env.name}-"
    ) as f:
        f.write(yaml_content)
        tmp_path = f.name

    try:
        cmd = [exe, "env", "create", "-f", tmp_path, "--yes"]
        console.print(f"Running: [dim]{' '.join(cmd)}[/dim]\n")
        subprocess.run(cmd, check=True)
        console.print(
            f"\n[green]Success![/green] Environment [bold]{env.name}[/bold] installed."
        )
        console.print(f"Activate it with: [bold cyan]conda activate {env.name}[/bold cyan]")
    finally:
        Path(tmp_path).unlink(missing_ok=True)
