"""Utility helpers for dtu-env."""

from __future__ import annotations

import shutil
import subprocess


def find_conda_executable() -> str | None:
    """find mamba or conda executable, preferring mamba"""
    for name in ("mamba", "conda"):
        path = shutil.which(name)
        if path:
            return path
    return None


def get_installed_environments() -> list[str]:
    """return list of installed conda environment names"""
    exe = find_conda_executable()
    if not exe:
        return []
    result = subprocess.run(
        [exe, "env", "list", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    import json
    data = json.loads(result.stdout)
    envs = []
    for env_path in data.get("envs", []):
        name = env_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        envs.append(name)
    return envs
