from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    output: Optional[Path] = None


@dataclass
class DownloadProgress:
    task_id: str
    downloaded: int
    total: Optional[int]
    speed_bps: float
    status: str
    name: str
    error: Optional[str] = None
