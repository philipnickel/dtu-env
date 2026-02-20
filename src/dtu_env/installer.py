"""Install conda environments for DTU courses."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import requests
from rich.console import Console

from dtu_env.api import CourseEnvironment


console = Console()

GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/dtudk/pythonsupport-page"
    "/main/docs/_static/environments"
)


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
    url = f"{GITHUB_RAW_URL}/{env.filename}"

    console.print(f"\nInstalling [bold cyan]{env.name}[/bold cyan] "
                  f"({env.course_full_name})...")
    console.print(f"Using: [dim]{Path(exe).stem}[/dim]")
    console.print(f"Source: [dim]{url}[/dim]\n")

    # Download the YAML to a temp file so conda can read it
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
        subprocess.run(cmd, check=True)
        console.print(
            f"\n[green]Success![/green] Environment [bold]{env.name}[/bold] installed."
        )
        console.print(f"Activate it with: [bold cyan]conda activate {env.name}[/bold cyan]")
    finally:
        Path(tmp_path).unlink(missing_ok=True)
