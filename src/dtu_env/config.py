"""Configuration constants for dtu-env."""

# GitHub repository serving course environment YAML files
GITHUB_USER = "dtudk"
GITHUB_REPO = "pythonsupport-page"
GITHUB_BRANCH = "main"
GITHUB_ENV_DIR = "docs/_static/environments"

# Constructed URLs
GITHUB_API_URL = (
    f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}"
    f"/contents/{GITHUB_ENV_DIR}?ref={GITHUB_BRANCH}"
)
GITHUB_RAW_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}"
    f"/{GITHUB_BRANCH}/{GITHUB_ENV_DIR}"
)
