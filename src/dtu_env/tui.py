"""Textual TUI for interactive course environment management."""

from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from dtu_env.api import fetch_all_environments
from dtu_env.installer import install_environment
from dtu_env.models import CourseEnvironment
from dtu_env.utils import get_installed_environments


# ---------------------------------------------------------------------------
# Home screen — shows installed environments
# ---------------------------------------------------------------------------

class HomeScreen(Screen):
    """main screen showing installed environments"""

    CSS = """
    #home-content {
        padding: 1 2;
    }
    #installed-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #installed-list {
        height: 1fr;
        margin-bottom: 1;
    }
    #install-btn {
        margin-top: 1;
    }
    .env-item {
        padding: 0 1;
    }
    #home-status {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("i", "install_new", "Install new"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="home-content"):
            yield Label("Installed Conda Environments", id="installed-title")
            yield ListView(id="installed-list")
            yield Button("Install course environments", id="install-btn", variant="primary")
        yield Static("[dim]i Install new | r Refresh | q Quit[/dim]", id="home-status")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_installed()

    @work(thread=True)
    def refresh_installed(self) -> None:
        self.call_from_thread(
            self.query_one("#home-status", Static).update,
            "Loading installed environments...",
        )
        installed = get_installed_environments()
        self.call_from_thread(self._populate_installed, installed)

    def _populate_installed(self, envs: list[str]) -> None:
        lv = self.query_one("#installed-list", ListView)
        lv.clear()
        if not envs:
            lv.append(ListItem(Label("[dim]No environments found[/dim]")))
        else:
            for name in envs:
                lv.append(ListItem(Label(f"  {name}", classes="env-item")))
        self.query_one("#home-status", Static).update(
            f"[dim]{len(envs)} environments installed | i Install new | r Refresh | q Quit[/dim]"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "install-btn":
            self.app.push_screen(InstallScreen())

    def action_install_new(self) -> None:
        self.app.push_screen(InstallScreen())

    def action_refresh(self) -> None:
        self.refresh_installed()

    def action_quit_app(self) -> None:
        self.app.exit()


# ---------------------------------------------------------------------------
# Install screen — fetch available envs, multi-select, install
# ---------------------------------------------------------------------------

class EnvCheckbox(Horizontal):
    """a checkbox row for a course environment"""

    DEFAULT_CSS = """
    EnvCheckbox {
        height: 1;
        padding: 0 1;
    }
    EnvCheckbox .env-name {
        width: 16;
        text-style: bold;
        color: $text;
    }
    EnvCheckbox .env-course {
        width: 1fr;
    }
    EnvCheckbox .env-semester {
        width: 20;
        color: $text-muted;
    }
    """

    def __init__(self, env: CourseEnvironment) -> None:
        super().__init__()
        self.env = env

    def compose(self) -> ComposeResult:
        yield Checkbox(self.env.name, value=False)
        yield Label(self.env.course_full_name, classes="env-course")
        yield Label(
            f"{self.env.course_semester} {self.env.course_year}",
            classes="env-semester",
        )


class InstallScreen(Screen):
    """screen for browsing and installing course environments"""

    CSS = """
    #install-content {
        padding: 1 2;
    }
    #install-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #search {
        margin-bottom: 1;
    }
    #env-scroll {
        height: 1fr;
        margin-bottom: 1;
    }
    #btn-bar {
        height: 3;
        align-horizontal: left;
    }
    #btn-bar Button {
        margin-right: 1;
    }
    #install-status {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("a", "select_all", "Select all"),
        Binding("n", "select_none", "Select none"),
    ]

    environments: list[CourseEnvironment] = []
    installed_names: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="install-content"):
            yield Label("Install Course Environments", id="install-title")
            yield Input(
                placeholder="Filter by course number, name, or semester...",
                id="search",
            )
            yield VerticalScroll(id="env-scroll")
            with Horizontal(id="btn-bar"):
                yield Button("Install selected", id="do-install", variant="primary")
                yield Button("Back", id="go-back", variant="default")
        yield Static("[dim]Loading...[/dim]", id="install-status")
        yield Footer()

    def on_mount(self) -> None:
        self.fetch_environments()

    @work(thread=True)
    def fetch_environments(self) -> None:
        self.call_from_thread(
            self.query_one("#install-status", Static).update,
            "Fetching available environments from GitHub...",
        )
        try:
            envs = fetch_all_environments()
            installed = get_installed_environments()
            self.call_from_thread(self._populate, envs, set(installed))
        except Exception as e:
            self.call_from_thread(
                self.query_one("#install-status", Static).update,
                f"[red]Error: {e}[/red]",
            )

    def _populate(self, envs: list[CourseEnvironment], installed: set[str]) -> None:
        self.environments = envs
        self.installed_names = installed
        self._render_list(envs)
        self.query_one("#install-status", Static).update(
            f"[dim]{len(envs)} available | a Select all | n None | Esc Back[/dim]"
        )

    def _render_list(self, envs: list[CourseEnvironment]) -> None:
        scroll = self.query_one("#env-scroll", VerticalScroll)
        scroll.remove_children()
        for env in envs:
            row = EnvCheckbox(env)
            scroll.mount(row)
            # Pre-check if already installed
            if env.name in self.installed_names:
                cb = row.query_one(Checkbox)
                cb.value = True
                cb.disabled = True
                cb.label = f"{env.name} [dim](installed)[/dim]"

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.strip().lower()
        if not query:
            filtered = self.environments
        else:
            filtered = [
                env for env in self.environments
                if query in env.name.lower()
                or query in env.course_number.lower()
                or query in env.course_full_name.lower()
                or query in env.course_semester.lower()
                or query in env.course_year.lower()
            ]
        self._render_list(filtered)

    def _get_selected_envs(self) -> list[CourseEnvironment]:
        selected = []
        for row in self.query(EnvCheckbox):
            cb = row.query_one(Checkbox)
            if cb.value and not cb.disabled:
                selected.append(row.env)
        return selected

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "do-install":
            self._install_selected()
        elif event.button.id == "go-back":
            self.app.pop_screen()

    def _install_selected(self) -> None:
        selected = self._get_selected_envs()
        if not selected:
            self.query_one("#install-status", Static).update(
                "[yellow]No environments selected[/yellow]"
            )
            return
        self._do_install(selected)

    @work(thread=True)
    def _do_install(self, envs: list[CourseEnvironment]) -> None:
        total = len(envs)
        succeeded = 0
        failed = 0

        for i, env in enumerate(envs, 1):
            self.call_from_thread(
                self.query_one("#install-status", Static).update,
                f"[yellow]Installing {env.name} ({i}/{total})...[/yellow]",
            )

            with self.app.suspend():
                success = install_environment(env)

            if success:
                succeeded += 1
                self.call_from_thread(self.installed_names.add, env.name)
            else:
                failed += 1

        # Refresh the checkboxes to show newly installed
        self.call_from_thread(self._render_list, self.environments)

        summary = f"[green]{succeeded} installed[/green]"
        if failed:
            summary += f", [red]{failed} failed[/red]"
        self.call_from_thread(
            self.query_one("#install-status", Static).update,
            f"Done: {summary} | Esc to go back",
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_select_all(self) -> None:
        for row in self.query(EnvCheckbox):
            cb = row.query_one(Checkbox)
            if not cb.disabled:
                cb.value = True

    def action_select_none(self) -> None:
        for row in self.query(EnvCheckbox):
            cb = row.query_one(Checkbox)
            if not cb.disabled:
                cb.value = False


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

class DtuEnvApp(App):
    """DTU course environment manager"""

    TITLE = "DTU Course Environments"
    SUB_TITLE = "dtu-env"

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())


def run_tui() -> None:
    """launch the interactive TUI"""
    app = DtuEnvApp()
    app.run()
