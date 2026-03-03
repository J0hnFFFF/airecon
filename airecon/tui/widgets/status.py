"""Status bar widget: connection indicators, model info."""

from __future__ import annotations

from textual.widgets import Label
from textual.containers import Horizontal
from textual.reactive import reactive

class StatusBar(Horizontal):
    """Bottom status bar."""

    DEFAULT_CSS = ""  # Defer to styles.tcss

    ollama_status = reactive("offline")
    docker_status = reactive("offline")
    model_name = reactive("—")
    exec_used = reactive(0)
    subagents_spawned = reactive(0)

    def compose(self):
        yield Label(id="status-text")

    def on_mount(self) -> None:
        self._update_display()

    def _get_status_text(self) -> str:
        ollama_dot = "●" if self.ollama_status == "online" else "○"
        ollama_color = "#00d4aa" if self.ollama_status == "online" else "#ef4444"

        docker_dot = "●" if self.docker_status == "online" else "○"
        docker_color = "#00d4aa" if self.docker_status == "online" else "#ef4444"

        subagent_part = (
            f"  │ [#8b949e]Agents:[/] [#a78bfa]{self.subagents_spawned}[/]"
            if self.subagents_spawned > 0 else ""
        )
        return (
            f" [{ollama_color}]{ollama_dot}[/] Ollama  "
            f"[{docker_color}]{docker_dot}[/] Docker  "
            f"│ [#8b949e]Model:[/] [#00d4aa]{self.model_name}[/]  "
            f"│ [#8b949e]Exec:[/] [#f59e0b]{self.exec_used}[/]"
            f"{subagent_part}  "
            f"│ [#484f58]Ctrl+C quit · Ctrl+L clear[/]"
        )

    def watch_ollama_status(self, _) -> None: self._update_display()
    def watch_docker_status(self, _) -> None: self._update_display()
    def watch_model_name(self, _) -> None: self._update_display()
    def watch_exec_used(self, _) -> None: self._update_display()
    def watch_subagents_spawned(self, _) -> None: self._update_display()

    def _update_display(self) -> None:
        try:
            self.query_one("#status-text", Label).update(self._get_status_text())
        except Exception:
            pass

    def set_status(
        self,
        ollama: str | None = None,
        docker: str | None = None,
        model: str | None = None,
        tools: int | None = None,
        exec_used: int | None = None,
        subagents: int | None = None,
    ) -> None:
        if ollama is not None:
            self.ollama_status = ollama
        if docker is not None:
            self.docker_status = docker
        if model is not None:
            self.model_name = model
        if exec_used is not None:
            self.exec_used = exec_used
        if subagents is not None:
            self.subagents_spawned = subagents
