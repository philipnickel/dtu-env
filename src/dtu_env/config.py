"""Configuration constants for dtu-env."""

# GitHub repository serving course environment YAML files
GITHUB_USER = "dtudk"
GITHUB_REPO = "pythonsupport-page"
GITHUB_BRANCH = "main"
GITHUB_ENV_DIR = "docs/_static/environments"

# Raw URL for fetching YAML files (no API, no rate limits)
GITHUB_RAW_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}"
    f"/{GITHUB_BRANCH}/{GITHUB_ENV_DIR}"
)
