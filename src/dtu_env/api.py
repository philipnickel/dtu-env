"""Fetch course environment data from GitHub."""

from __future__ import annotations

import os

import requests
import yaml

from dtu_env.config import GITHUB_API_URL, GITHUB_RAW_URL
from dtu_env.models import CourseEnvironment


def _api_headers() -> dict[str, str]:
    """build headers for GitHub API requests, using token if available"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def _handle_rate_limit(response) -> None:
    """check if response is rate limited and raise helpful error"""
    if response.status_code == 403:
        # Check if it's a rate limit (vs other 403)
        try:
            data = response.json()
            if "rate limit" in data.get("message", "").lower():
                raise RuntimeError(
                    "GitHub API rate limit exceeded (60 requests/hour). "
                    "Set GITHUB_TOKEN environment variable for 5000 requests/hour."
                )
        except (ValueError, AttributeError):
            pass


def fetch_environment_list() -> list[str]:
    """fetch the list of .yml filenames from the GitHub environments directory"""
    response = requests.get(GITHUB_API_URL, headers=_api_headers(), timeout=15)
    
    _handle_rate_limit(response)
    response.raise_for_status()
    
    entries = response.json()
    return sorted(
        entry["name"]
        for entry in entries
        if isinstance(entry, dict) and entry.get("name", "").endswith(".yml")
    )


def fetch_environment_yaml(filename: str) -> dict:
    """fetch and parse a single environment YAML file via raw.githubusercontent.com"""
    url = f"{GITHUB_RAW_URL}/{filename}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return yaml.safe_load(response.text)


def parse_environment(data: dict, filename: str) -> CourseEnvironment:
    """parse a YAML dict into a CourseEnvironment"""
    meta = data.get("metadata", {})
    return CourseEnvironment(
        name=str(data.get("name", filename.removesuffix(".yml"))),
        course_number=meta.get("course_number", ""),
        course_full_name=meta.get("course_full_name", ""),
        course_year=meta.get("course_year", ""),
        course_semester=meta.get("course_semester", ""),
        channels=data.get("channels", []),
        dependencies=data.get("dependencies", []),
        filename=filename,
    )


def fetch_all_environments() -> list[CourseEnvironment]:
    """fetch and parse all available course environments"""
    filenames = fetch_environment_list()
    environments = []
    for filename in filenames:
        data = fetch_environment_yaml(filename)
        environments.append(parse_environment(data, filename))
    return environments
