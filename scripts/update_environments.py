#!/usr/bin/env python3
"""Fetch environment metadata from GitHub and update bundled JSON."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml


GITHUB_API_URL = "https://api.github.com/repos/dtudk/pythonsupport-page/contents/docs/_static/environments?ref=main"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/dtudk/pythonsupport-page/main/docs/_static/environments"


def fetch_filenames() -> list[str]:
    """Fetch list of .yml files from GitHub."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    
    response = requests.get(GITHUB_API_URL, headers=headers, timeout=15)
    response.raise_for_status()
    
    entries = response.json()
    return sorted(
        entry["name"]
        for entry in entries
        if isinstance(entry, dict) and entry.get("name", "").endswith(".yml")
    )


def fetch_yaml(filename: str) -> dict:
    """Fetch and parse a single YAML file."""
    url = f"{GITHUB_RAW_URL}/{filename}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return yaml.safe_load(response.text)


def main():
    print("Fetching environment list...")
    filenames = fetch_filenames()
    print(f"Found {len(filenames)} environments")
    
    environments = []
    for filename in filenames:
        print(f"  Processing {filename}...")
        data = fetch_yaml(filename)
        meta = data.get("metadata", {})
        
        environments.append({
            "name": str(data.get("name", filename.removesuffix(".yml"))),
            "course_number": meta.get("course_number", ""),
            "course_full_name": meta.get("course_full_name", ""),
            "course_year": meta.get("course_year", ""),
            "course_semester": meta.get("course_semester", ""),
            "filename": filename,
            "channels": data.get("channels", []),
            "dependencies": data.get("dependencies", []),
        })
    
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environments": environments,
    }
    
    # Write to src/dtu_env/data/environments.json
    data_dir = Path(__file__).parent.parent / "src" / "dtu_env" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = data_dir / "environments.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nWrote {len(environments)} environments to {output_file}")
    
    # Also create __init__.py for data package
    init_file = data_dir / "__init__.py"
    init_file.touch(exist_ok=True)


if __name__ == "__main__":
    main()
