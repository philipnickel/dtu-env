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

    @property
    def display_name(self) -> str:
        """human-readable display string"""
        return f"{self.course_number} - {self.course_full_name} ({self.course_semester} {self.course_year})"

    @property
    def short_label(self) -> str:
        """short label for menus"""
        return f"[bold]{self.name}[/bold]  {self.course_full_name}"
