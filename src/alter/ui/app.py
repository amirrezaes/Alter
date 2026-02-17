from __future__ import annotations

from typing import Iterable, Optional

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Label, ListItem, ListView, ProgressBar, Static

from alter.core.downloader import DownloadManager, TaskConfig
from alter.core.formatting import format_bytes
from alter.core.models import DownloadProgress, DownloadRequest
from alter.ui.screens import AddDownloadScreen, RemoveDownloadScreen


class DownloadRow(ListItem):
    def __init__(self, task_id: str, name: str, url: str) -> None:
        super().__init__()
        self.add_class("download-row")
        self.task_id = task_id
        self.display_name = name
        self.display_url = url
        self._status_label: Optional[Label] = None
        self._progress_label: Optional[Label] = None
        self._speed_label: Optional[Label] = None
        self._bar: Optional[ProgressBar] = None

    def compose(self) -> ComposeResult:
        name = Label(self.display_name, classes="name")
        status = Label("queued", classes="status")
        bar = ProgressBar(total=100, show_eta=False, show_percentage=False, id="bar")
        speed = Label("0 B/s", classes="speed")
        progress = Label("0%", classes="progress")

        self._status_label = status
        self._progress_label = progress
        self._speed_label = speed
        self._bar = bar

        yield Container(name, status, bar, speed, progress, classes="row")

    def update_from_progress(self, progress: DownloadProgress) -> None:
        if self._status_label:
            status = progress.status
            if progress.error:
                status = f"error: {progress.error}"
            self._status_label.update(status)
        if self._progress_label:
            if progress.total:
                percent = (progress.downloaded / progress.total) * 100
                details = f"{format_bytes(progress.downloaded)} / {format_bytes(progress.total)}"
                self._progress_label.update(f"{percent:0.1f}% ({details})")
                if self._bar:
                    self._bar.total = 100
                    self._bar.progress = percent
            else:
                self._progress_label.update(f"{format_bytes(progress.downloaded)}")
                if self._bar:
                    self._bar.total = 1
                    self._bar.progress = 0
        if self._speed_label:
            self._speed_label.update(f"{format_bytes(int(progress.speed_bps))}/s")


class DownloadApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #downloads {
        height: 1fr;
    }

    .download-row {
        height: 6;
    }

    .row {
        layout: grid;
        grid-size: 2 3;
        grid-columns: 1fr auto;
        grid-rows: auto auto auto;
        padding: 0 2;
        border: heavy $accent;
        margin: 0 2;
    }

    .name {
        text-style: bold;
    }

    .status {
        text-align: right;
    }

    .speed {
        text-align: right;
        color: $success;
    }

    .progress {
        column-span: 2;
        text-align: center;
        color: $text-muted;
    }

    #bar {
        height: 1;
    }

    #hint {
        padding: 0 2;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("a", "add", "Add"),
        ("p", "pause", "Pause/Resume"),
        ("s", "stop", "Stop"),
        ("d", "remove", "Remove"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, initial: Iterable[DownloadRequest], config: Optional[TaskConfig] = None) -> None:
        super().__init__()
        self._manager = DownloadManager(config=config, progress_callback=self._handle_progress)
        self._rows: dict[str, DownloadRow] = {}
        self._initial = list(initial)

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(id="downloads")
        yield Static("A=Add  P=Pause/Resume  S=Stop  D=Remove  Q=Quit", id="hint")
        yield Footer()

    def on_mount(self) -> None:
        for request in self._initial:
            self._add_and_start(request)

    def _handle_progress(self, progress: DownloadProgress) -> None:
        self._update_row(progress)

    def _update_row(self, progress: DownloadProgress) -> None:
        row = self._rows.get(progress.task_id)
        if row:
            row.update_from_progress(progress)

    def _get_selected_row(self) -> Optional[DownloadRow]:
        list_view = self.query_one("#downloads", ListView)
        row = list_view.highlighted_child
        return row if isinstance(row, DownloadRow) else None

    def _add_and_start(self, request: DownloadRequest) -> None:
        task = self._manager.add(request)
        row = DownloadRow(task.id, task.name, task.url)
        self._rows[task.id] = row
        self.query_one("#downloads", ListView).append(row)
        self._manager.start(task.id)

    def action_add(self) -> None:
        self.push_screen(AddDownloadScreen(), self._handle_add_result)

    def _handle_add_result(self, result: Optional[DownloadRequest]) -> None:
        if result:
            self._add_and_start(result)

    def action_pause(self) -> None:
        row = self._get_selected_row()
        if not row:
            return
        task = self._manager.get(row.task_id)
        if not task:
            return
        if task.status == "paused":
            self._manager.resume(task.id)
        elif task.status == "downloading":
            self._manager.pause(task.id)

    def action_stop(self) -> None:
        row = self._get_selected_row()
        if row:
            self._manager.stop(row.task_id)

    def action_remove(self) -> None:
        row = self._get_selected_row()
        if not row:
            return
        task = self._manager.get(row.task_id)
        if not task:
            return
        self.push_screen(
            RemoveDownloadScreen(task.name, task.output),
            lambda result: self._handle_remove_result(row.task_id, task.output, result)
        )

    def _handle_remove_result(self, task_id: str, file_path, remove_file: Optional[bool]) -> None:
        if remove_file is None:
            return  # User cancelled
        
        # Stop and remove the task
        self._manager.stop(task_id)
        self._manager.remove(task_id)
        
        # Remove the row from UI
        row = self._rows.get(task_id)
        if row:
            row.remove()
            self._rows.pop(task_id, None)
        
        # Delete the file if requested
        if remove_file:
            try:
                from pathlib import Path
                path = Path(file_path)
                if path.exists() and path.is_file():
                    path.unlink()
            except Exception:
                # If file deletion fails, just continue (entry is already removed)
                pass
