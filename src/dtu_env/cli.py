"""CLI entry point for dtu-env."""

from __future__ import annotations

import sys

from dtu_env import __version__


def main() -> int:
    # Only handle --version / --help, everything else is the TUI
    if len(sys.argv) > 1 and sys.argv[1] in ("-V", "--version"):
        print(f"dtu-env {__version__}")
        return 0
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("dtu-env — DTU Course Environment Manager")
        print()
        print("Usage: dtu-env")
        print()
        print("Launches an interactive browser to view installed")
        print("environments and install new course environments.")
        print()
        print("Options:")
        print("  -V, --version  Show version and exit")
        print("  -h, --help     Show this help and exit")
        return 0

    from dtu_env.tui import run_tui
    run_tui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
