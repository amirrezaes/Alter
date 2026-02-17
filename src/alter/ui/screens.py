from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

from alter.core.models import DownloadRequest


class AddDownloadScreen(ModalScreen[Optional[DownloadRequest]]):
    CSS = """
    #dialog {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
        align: center middle;
    }

    #title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #buttons {
        width: 100%;
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Add Download", id="title"),
            Input(placeholder="URL", id="url"),
            Input(placeholder="Output path (optional)", id="output"),
            Horizontal(
                Button("Add", id="confirm", variant="primary"),
                Button("Cancel", id="cancel"),
                id="buttons",
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return

        url = self.query_one("#url", Input).value.strip()
        output = self.query_one("#output", Input).value.strip()
        if not url:
            self.query_one("#title", Label).update("Add Download - URL required")
            return

        output_path = Path(output) if output else None
        self.dismiss(DownloadRequest(url=url, output=output_path))


class RemoveDownloadScreen(ModalScreen[Optional[bool]]):
    """Modal screen to confirm download removal.
    
    Returns:
        True - Remove entry and delete file
        False - Remove entry only
        None - Cancel (don't remove anything)
    """
    
    CSS = """
    #dialog {
        width: 70;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
        align: center middle;
    }

    #title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #message {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    #filepath {
        color: $text-muted;
        margin-top: 1;
    }

    #buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, download_name: str, file_path: Path) -> None:
        super().__init__()
        self.download_name = download_name
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Remove Download", id="title"),
            Vertical(
                Label(f"Remove '{self.download_name}'?"),
                Label(f"File: {self.file_path}", id="filepath"),
                id="message"
            ),
            Horizontal(
                Button("Remove Entry Only", id="entry_only", variant="primary"),
                Button("Remove File Too", id="with_file", variant="error"),
                Button("Cancel", id="cancel"),
                id="buttons",
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "entry_only":
            self.dismiss(False)
        elif event.button.id == "with_file":
            self.dismiss(True)
