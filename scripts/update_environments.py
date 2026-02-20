#!/usr/bin/env python3
"""Fetch environment YAML files from GitHub and bundle them."""

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


def fetch_yaml(filename: str) -> str:
    """Fetch raw YAML file content."""
    url = f"{GITHUB_RAW_URL}/{filename}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text


def main():
    print("Fetching environment list...")
    filenames = fetch_filenames()
    print(f"Found {len(filenames)} environments")
    
    # Create environments directory
    env_dir = Path(__file__).parent.parent / "src" / "dtu_env" / "environments"
    env_dir.mkdir(parents=True, exist_ok=True)
    
    environments = []
    for filename in filenames:
        print(f"  Processing {filename}...")
        
        # Fetch and save YAML file
        yaml_content = fetch_yaml(filename)
        yaml_path = env_dir / filename
        with open(yaml_path, "w") as f:
            f.write(yaml_content)
        
        # Parse for metadata
        data = yaml.safe_load(yaml_content)
        meta = data.get("metadata", {})
        
        environments.append({
            "name": str(data.get("name", filename.removesuffix(".yml"))),
            "course_number": meta.get("course_number", ""),
            "course_full_name": meta.get("course_full_name", ""),
            "course_year": meta.get("course_year", ""),
            "course_semester": meta.get("course_semester", ""),
            "filename": filename,
        })
    
    # Write metadata JSON
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environments": environments,
    }
    
    json_path = Path(__file__).parent.parent / "src" / "dtu_env" / "environments.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nWrote {len(environments)} YAML files to {env_dir}")
    print(f"Wrote metadata to {json_path}")


if __name__ == "__main__":
    main()
