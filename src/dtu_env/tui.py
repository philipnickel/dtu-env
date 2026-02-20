"""Simple interactive CLI for course environment management."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

from rich.console import Console
from simple_term_menu import TerminalMenu

from dtu_env import __version__
from dtu_env.api import fetch_all_environments
from dtu_env.installer import install_environment

console = Console()

MENU_STYLE = {
    "menu_cursor_style": ("fg_cyan", "bold"),
    "menu_highlight_style": ("fg_cyan", "bold"),
}


def _get_installed_environments() -> list[str]:
    """return list of installed conda environment names"""
    # find conda/mamba executable
    exe = None
    for name in ("mamba", "conda"):
        exe = shutil.which(name)
        if exe:
            break
    if not exe:
        return []
    result = subprocess.run(
        [exe, "env", "list", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    data = json.loads(result.stdout)
    envs = []
    for env_path in data.get("envs", []):
        name = env_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        envs.append(name)
    return envs


def _header():
    """print the app header"""
    console.print()
    console.print(f"  [bold cyan]dtu-env[/bold cyan] [dim]v{__version__}[/dim]")
    console.print(f"  [dim]DTU Course Environment Manager[/dim]")
    console.print()


def _fetch_environments():
    """fetch available environments with a spinner"""
    with console.status("[bold cyan]Fetching available environments from GitHub..."):
        try:
            envs = fetch_all_environments()
        except Exception as e:
            console.print(f"\n  [red]Error fetching environments:[/red] {e}")
            return []
    return envs


def _pick_year(envs):
    """let user pick a year, sorted newest first. return year string or None"""
    years = sorted({e.course_year for e in envs}, reverse=True)
    if not years:
        return None
    options = years + ["Back"]
    menu = TerminalMenu(options, title="  Select year:", **MENU_STYLE)
    choice = menu.show()
    if choice is None or choice == len(years):
        return None
    return years[choice]


def _pick_semester(envs, year):
    """let user pick a semester for the given year. return semester string or None"""
    # collect semesters available for this year
    semesters = set()
    for e in envs:
        if e.course_year != year:
            continue
        sem = e.course_semester.lower()
        if "autumn" in sem:
            semesters.add("Autumn")
        if "spring" in sem:
            semesters.add("Spring")

    # stable order: Spring before Autumn
    ordered = [s for s in ["Spring", "Autumn"] if s in semesters]
    if not ordered:
        return None
    options = ordered + ["Back"]
    menu = TerminalMenu(options, title=f"  Select semester ({year}):", **MENU_STYLE)
    choice = menu.show()
    if choice is None or choice == len(ordered):
        return None
    return ordered[choice]


def _pick_courses(envs, year, semester, installed_names):
    """let user multi-select courses for year+semester. return list of CourseEnvironments"""
    # filter: match year, and semester must contain the chosen semester
    filtered = [
        e for e in envs
        if e.course_year == year and semester.lower() in e.course_semester.lower()
    ]
    if not filtered:
        console.print("  [dim]No courses found for this selection.[/dim]")
        return []

    # sort by course number
    filtered.sort(key=lambda e: e.course_number)

    # build menu entries: "01002 - Mathematics 1b"  or  "01002 - Mathematics 1b (installed)"
    entries = []
    preselected = []
    for i, env in enumerate(filtered):
        tag = " (installed)" if env.name in installed_names else ""
        entries.append(f"{env.course_number} - {env.course_full_name}{tag}")
        if env.name in installed_names:
            preselected.append(i)

    console.print(f"  [dim]{len(filtered)} courses available for {semester} {year}[/dim]")
    console.print(f"  [dim]space=toggle  enter=confirm  q/esc=back[/dim]")
    console.print()

    menu = TerminalMenu(
        entries,
        title=f"  Select courses ({semester} {year}):",
        multi_select=True,
        show_multi_select_hint=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=True,
        preselected_entries=preselected if preselected else None,
        **MENU_STYLE,
    )
    chosen = menu.show()

    if chosen is None:
        return []
    if isinstance(chosen, int):
        chosen = (chosen,)

    # filter out already-installed
    selected = []
    for idx in chosen:
        env = filtered[idx]
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
        try:
            install_environment(env)
            succeeded += 1
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")
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
        while True:
            console.clear()
            _header()

            installed = _get_installed_environments()
            if installed:
                console.print("  [bold]Installed conda environments:[/bold]")
                console.print()
                for name in installed:
                    console.print(f"    {name}")
            else:
                console.print("  [dim]No conda environments found.[/dim]")
            console.print()

            menu = TerminalMenu(
                ["Install additional environments", "Quit"],
                title="  What would you like to do?",
                **MENU_STYLE,
            )
            choice = menu.show()

            if choice != 0:
                console.print()
                console.print("  [dim]Bye![/dim]")
                break

            # fetch all environments once
            console.print()
            envs = _fetch_environments()
            if not envs:
                console.print("  [dim]No environments available. Press enter to continue...[/dim]")
                input()
                continue

            installed_names = set(installed)

            # drill-down: year -> semester -> courses
            year = _pick_year(envs)
            if year is None:
                continue

            semester = _pick_semester(envs, year)
            if semester is None:
                continue

            selected = _pick_courses(envs, year, semester, installed_names)
            if not selected:
                console.print("\n  [dim]Nothing to install.[/dim]")
                console.print("  [dim]Press enter to continue...[/dim]")
                input()
                continue

            # confirm
            console.print()
            names = ", ".join(e.name for e in selected)
            console.print(f"  Will install: [bold cyan]{names}[/bold cyan]")
            confirm_menu = TerminalMenu(
                ["Yes, install", "Cancel"],
                title="  Proceed?",
                **MENU_STYLE,
            )
            if confirm_menu.show() != 0:
                continue

            _install_selected(selected)
            console.print("  [dim]Press enter to continue...[/dim]")
            input()
    except KeyboardInterrupt:
        console.print("\n  [dim]Bye![/dim]")
        sys.exit(0)
