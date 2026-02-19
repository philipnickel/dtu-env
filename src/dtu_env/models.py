"""Data models for course environments."""

from __future__ import annotations

from dataclasses import dataclass, field


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
