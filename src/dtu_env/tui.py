"""Simple interactive CLI for course environment management."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

from rich.console import Console
from rich.prompt import Prompt
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
    with console.status("[bold cyan]Loading available courses..."):
        try:
            envs = fetch_all_environments()
        except Exception as e:
            console.print(f"\n  [red]Error loading courses:[/red] {e}")
            return []
    return envs


def _get_unique_courses(envs):
    """get list of unique courses (number, name) tuples"""
    seen = set()
    courses = []
    for e in envs:
        key = (e.course_number, e.course_full_name)
        if key not in seen:
            seen.add(key)
            courses.append(key)
    return sorted(courses)


def _pick_course(courses):
    """let user pick a course from list with live search. return (number, name) or None"""
    if not courses:
        console.print("  [dim]No courses available.[/dim]")
        return None
    
    # format: "01002 - Mathematics 1b"
    options = [f"{num} - {name}" for num, name in courses] + ["Back"]
    
    console.print(f"  [dim]Start typing to search ({len(courses)} courses)[/dim]")
    console.print(f"  [dim]e.g., type '01002' or 'math' to filter[/dim]")
    console.print()
    
    menu = TerminalMenu(
        options,
        title="  Select course:",
        search_key=None,  # enables live search with any key
        show_search_hint=True,
        **MENU_STYLE,
    )
    choice = menu.show()
    
    if choice is None or choice == len(courses):
        return None
    return courses[choice]


def _pick_versions(envs, course_number, installed_names):
    """let user pick version(s) of a course. return list of CourseEnvironments"""
    # filter all versions of this course
    versions = [e for e in envs if e.course_number == course_number]
    # sort by year (newest first) then semester
    versions.sort(key=lambda e: (e.course_year, e.course_semester), reverse=True)
    
    if not versions:
        return []
    
    # format: "2025 Spring" or "2024 Autumn (installed)"
    entries = []
    preselected = []
    for i, env in enumerate(versions):
        tag = " (installed)" if env.name in installed_names else ""
        entries.append(f"{env.course_year} {env.course_semester}{tag}")
        if env.name in installed_names:
            preselected.append(i)
    
    console.print(f"  [dim]{len(versions)} version(s) available[/dim]")
    console.print(f"  [dim]space=toggle  enter=confirm  q/esc=back[/dim]")
    console.print()
    
    menu = TerminalMenu(
        entries,
        title="  Select version(s) to install:",
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
        env = versions[idx]
        if env.name not in installed_names:
            selected.append(env)
    
    return selected


def _validate_env_name(name: str) -> tuple[bool, str]:
    """validate env name. returns (is_valid, error_message)."""
    if not name.strip():
        return False, "Name cannot be empty"
    if " " in name:
        return False, "Name cannot contain spaces"
    return True, ""


def _rename_environments(envs):
    """prompt for rename with validation. returns list of (env, new_name)."""
    renamed = []
    for env in envs:
        while True:
            # show: "Rename environment 01001_A24 (01001 - Mathematics 1a)?"
            prompt_text = f"Rename environment [bold]{env.name}[/bold] ({env.course_number} - {env.course_full_name})?"
            console.print(f"\n  {prompt_text}")

            new_name = Prompt.ask(
                "  New name",
                default=env.name,
                show_default=False,
            )

            # if empty (just Enter), use original name
            if not new_name.strip():
                final_name = env.name
                renamed.append((env, final_name))
                break

            is_valid, error = _validate_env_name(new_name)
            if is_valid:
                renamed.append((env, new_name))
                break
            else:
                console.print(f"  [red]Error: {error}[/red]")
                console.print("  [dim]Please try again[/dim]")

    return renamed


def _show_install_summary(renamed_envs):
    """show proceed confirmation with renamed environments."""
    console.print()
    console.print("  Will install:")
    for env, new_name in renamed_envs:
        if new_name != env.name:
            console.print(f"    [bold cyan]{new_name}[/bold cyan] [dim](was: {env.name})[/dim]")
        else:
            console.print(f"    [bold cyan]{env.name}[/bold cyan] [dim](unchanged)[/dim]")
    console.print()

    confirm_menu = TerminalMenu(
        ["Yes, install", "Cancel"],
        title="  Proceed?",
        **MENU_STYLE,
    )
    return confirm_menu.show() == 0


def _install_selected(renamed_envs):
    """install the selected environments one by one with potential new names."""
    total = len(renamed_envs)
    succeeded = 0
    failed = 0

    for i, (env, new_name) in enumerate(renamed_envs, 1):
        console.print()
        if new_name != env.name:
            console.rule(f"[bold cyan]Installing {new_name} ({i}/{total})[/bold cyan] [dim](from {env.name})[/dim]")
        else:
            console.rule(f"[bold cyan]Installing {env.name} ({i}/{total})[/bold cyan]")

        try:
            # create modified env object with new name for installer
            from dataclasses import replace
            env_to_install = replace(env, name=new_name)
            install_environment(env_to_install)
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

            # load all environments
            console.print()
            envs = _fetch_environments()
            if not envs:
                console.print("  [dim]No environments available. Press enter to continue...[/dim]")
                input()
                continue

            # get unique courses and pick one
            courses = _get_unique_courses(envs)
            course = _pick_course(courses)
            if course is None:
                continue
            
            # select versions
            installed_names = set(installed)
            selected = _pick_versions(envs, course[0], installed_names)
            
            if not selected:
                console.print("\n  [dim]Nothing to install.[/dim]")
                console.print("  [dim]Press enter to continue...[/dim]")
                input()
                continue

            # rename environments
            console.print()
            console.print("  [dim]Press Enter to keep current name, or type a new name (no spaces)[/dim]")
            renamed = _rename_environments(selected)
            
            # confirm and install
            if not _show_install_summary(renamed):
                continue

            _install_selected(renamed)
            console.print("  [dim]Press enter to continue...[/dim]")
            input()
    except KeyboardInterrupt:
        console.print("\n  [dim]Bye![/dim]")
        sys.exit(0)
