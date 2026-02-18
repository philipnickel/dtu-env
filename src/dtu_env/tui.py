"""Simple interactive CLI for course environment management."""

from __future__ import annotations

import sys

from rich.console import Console
from simple_term_menu import TerminalMenu

from dtu_env import __version__
from dtu_env.api import fetch_all_environments
from dtu_env.installer import install_environment
from dtu_env.utils import get_installed_environments

console = Console()


def _header():
    """print the app header"""
    console.print()
    console.print(f"  [bold cyan]dtu-env[/bold cyan] [dim]v{__version__}[/dim]")
    console.print(f"  [dim]DTU Course Environment Manager[/dim]")
    console.print()


def _action_menu():
    """show the action menu after displaying installed envs"""
    options = [
        "Install additional environments",
        "Quit",
    ]
    menu = TerminalMenu(
        options,
        title="  What would you like to do?",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("fg_cyan", "bold"),
    )
    return menu.show()


def _fetch_environments():
    """fetch available environments with a spinner"""
    with console.status("[bold cyan]Fetching available environments from GitHub..."):
        try:
            envs = fetch_all_environments()
        except Exception as e:
            console.print(f"\n  [red]Error fetching environments:[/red] {e}")
            return []
    return envs


def _build_menu_entries(envs, installed_names):
    """build display strings for the multi-select menu"""
    entries = []
    for env in envs:
        tag = "[installed]" if env.name in installed_names else ""
        line = f"{env.name:<16} {env.course_full_name:<40} {env.course_semester} {env.course_year} {tag}"
        entries.append(line.rstrip())
    return entries


def _select_environments(envs, installed_names):
    """show a multi-select menu of available environments, return selected CourseEnvironments"""
    entries = _build_menu_entries(envs, installed_names)

    # Pre-select already-installed environments (shown as disabled context)
    preselected = [i for i, env in enumerate(envs) if env.name in installed_names]

    console.print(f"  [dim]{len(envs)} environments available[/dim]")
    console.print(f"  [dim]space=toggle  enter=confirm  q/esc=cancel[/dim]")
    console.print()

    menu = TerminalMenu(
        entries,
        title="  Select environments to install:",
        multi_select=True,
        show_multi_select_hint=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=True,
        preselected_entries=preselected,
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("fg_cyan", "bold"),
    )
    chosen = menu.show()

    if chosen is None:
        return []

    # chosen is a tuple of selected indices
    if isinstance(chosen, int):
        chosen = (chosen,)

    # Filter out already-installed
    selected = []
    for idx in chosen:
        env = envs[idx]
        if env.name not in installed_names:
            selected.append(env)

    return selected


def _install_selected(selected):
    """install the selected environments one by one"""
    total = len(selected)
    succeeded = 0
    failed = 0

    for i, env in enumerate(selected, 1):
        console.print()
        console.rule(f"[bold cyan]Installing {env.name} ({i}/{total})[/bold cyan]")
        success = install_environment(env)
        if success:
            succeeded += 1
        else:
            failed += 1

    console.print()
    summary = f"[green]{succeeded} installed[/green]"
    if failed:
        summary += f", [red]{failed} failed[/red]"
    console.print(f"  {summary}")
    console.print()


def run_tui():
    """launch the interactive environment manager"""
    try:
        _run_loop()
    except KeyboardInterrupt:
        console.print("\n  [dim]Bye![/dim]")
        sys.exit(0)


def _run_loop():
    """main interaction loop"""
    while True:
        console.clear()
        _header()

        installed = get_installed_environments()
        if installed:
            console.print("  [bold]Installed conda environments:[/bold]")
            console.print()
            for name in installed:
                console.print(f"    {name}")
        else:
            console.print("  [dim]No conda environments found.[/dim]")
        console.print()

        choice = _action_menu()

        if choice == 0:
            # Install additional environments
            console.print()
            envs = _fetch_environments()
            if not envs:
                console.print("  [dim]No environments available. Press enter to continue...[/dim]")
                input()
                continue

            installed_names = set(installed)
            selected = _select_environments(envs, installed_names)

            if not selected:
                console.print("\n  [dim]Nothing to install.[/dim]")
                console.print("  [dim]Press enter to continue...[/dim]")
                input()
                continue

            # Confirm
            console.print()
            names = ", ".join(e.name for e in selected)
            console.print(f"  Will install: [bold cyan]{names}[/bold cyan]")
            confirm_menu = TerminalMenu(
                ["Yes, install", "Cancel"],
                title="  Proceed?",
                menu_cursor_style=("fg_cyan", "bold"),
                menu_highlight_style=("fg_cyan", "bold"),
            )
            if confirm_menu.show() != 0:
                continue

            _install_selected(selected)
            console.print("  [dim]Press enter to continue...[/dim]")
            input()

        else:
            # Quit (index 1, None, or anything else)
            console.print()
            console.print("  [dim]Bye![/dim]")
            break
