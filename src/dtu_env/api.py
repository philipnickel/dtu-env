"""Fetch course environment data from bundled JSON."""

from __future__ import annotations

import json
from importlib.resources import files

import requests
import yaml

from dtu_env.config import GITHUB_RAW_URL
from dtu_env.models import CourseEnvironment


def _load_environments_json() -> dict:
    """Load bundled environments.json."""
    data_path = files("dtu_env.data").joinpath("environments.json")
    return json.loads(data_path.read_text())


def fetch_all_environments() -> list[CourseEnvironment]:
    """Load all environments from bundled JSON."""
    data = _load_environments_json()
    return [
        CourseEnvironment(
            name=e["name"],
            course_number=e["course_number"],
            course_full_name=e["course_full_name"],
            course_year=e["course_year"],
            course_semester=e["course_semester"],
            filename=e["filename"],
            channels=e.get("channels", []),
            dependencies=e.get("dependencies", []),
        )
        for e in data["environments"]
    ]


def fetch_environment_yaml(filename: str) -> dict:
    """Fetch a single YAML from raw GitHub (no API, no rate limit)."""
    url = f"{GITHUB_RAW_URL}/{filename}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return yaml.safe_load(response.text)
