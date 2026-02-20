"""Fetch course environment data from bundled JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib.resources import files


GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/dtudk/pythonsupport-page"
    "/main/docs/_static/environments"
)


@dataclass
class CourseEnvironment:
    """a single course environment parsed from a YAML file"""

    name: str
    course_number: str
    course_full_name: str
    course_year: str
    course_semester: str
    channels: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    filename: str = ""


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
