from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
import re
import shutil
import time
import urllib.parse
import uuid

import aiofiles
import aiohttp

from alter.core.models import DownloadProgress, DownloadRequest


DEFAULT_CHUNK_SIZE = 1024 * 1024
DEFAULT_PARTS = 6
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_CONNECTIONS = 4


@dataclass
class TaskConfig:
    parts: int = DEFAULT_PARTS
    chunk_size: int = DEFAULT_CHUNK_SIZE
    timeout: int = DEFAULT_TIMEOUT
    max_connections: int = DEFAULT_MAX_CONNECTIONS


def compute_ranges(size: int, parts: int) -> list[tuple[int, int]]:
    if size <= 0:
        return []
    parts = max(1, parts)
    base = size // parts
    remainder = size % parts
    ranges: list[tuple[int, int]] = []
    start = 0
    for index in range(parts):
        length = base + (1 if index < remainder else 0)
        if length == 0:
            break
        end = start + length - 1
        ranges.append((start, end))
        start = end + 1
    return ranges


def _default_output_path(task_id: str) -> Path:
    return Path(f"download-{task_id}.bin")


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters."""
    # Remove or replace characters that are invalid in filenames
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Ensure it's not empty
    return sanitized if sanitized else "download"


def _extract_filename_from_url(url: str) -> Optional[str]:
    """
    Extract filename from URL path if it has a proper name with extension.
    Returns None if no suitable filename is found.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path)
        
        # Get the last component of the path
        if not path or path == '/':
            return None
        
        filename = path.rstrip('/').split('/')[-1]
        
        # Check if it looks like a file (has an extension)
        if '.' in filename and not filename.startswith('.'):
            # Split into name and extension
            parts = filename.rsplit('.', 1)
            if len(parts) == 2 and parts[1] and len(parts[1]) <= 10:  # Reasonable extension length
                return _sanitize_filename(filename)
        
        return None
    except Exception:
        return None


def _extract_filename_from_headers(headers: dict) -> Optional[str]:
    """
    Extract filename from Content-Disposition header.
    Returns None if no filename is found.
    """
    content_disp = headers.get('Content-Disposition', '')
    if not content_disp:
        return None
    
    # Try to find filename* (RFC 5987) first
    match = re.search(r"filename\*=(?:UTF-8''|utf-8'')?([^;]+)", content_disp, re.IGNORECASE)
    if match:
        filename = urllib.parse.unquote(match.group(1).strip('\'"'))
        return _sanitize_filename(filename)
    
    # Try regular filename parameter
    match = re.search(r'filename="?([^";]+)"?', content_disp, re.IGNORECASE)
    if match:
        filename = match.group(1).strip('\'"')
        return _sanitize_filename(filename)
    
    return None


def _get_url_fallback_name(url: str) -> str:
    """
    Get a fallback filename from the last part of the URL.
    Always returns a valid filename.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path)
        
        # Get the last component
        if path and path != '/':
            last_part = path.rstrip('/').split('/')[-1]
            if last_part:
                sanitized = _sanitize_filename(last_part)
                if sanitized:
                    return sanitized
        
        # If path doesn't give us anything useful, try domain
        if parsed.netloc:
            domain = parsed.netloc.split(':')[0]  # Remove port if present
            return _sanitize_filename(domain)
        
        return "download"
    except Exception:
        return "download"


def _ensure_parent(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


class DownloadTask:
    def __init__(
        self,
        request: DownloadRequest,
        temp_root: Path,
        config: TaskConfig,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> None:
        self.id = uuid.uuid4().hex
        self.url = request.url
        
        # Smart filename extraction
        if request.output:
            self.output = request.output
            self._auto_named = False
        else:
            # Try to extract filename from URL
            filename = _extract_filename_from_url(request.url)
            if filename:
                self.output = Path(filename)
                self._auto_named = True  # May be updated from headers
            else:
                # Use fallback name
                filename = _get_url_fallback_name(request.url)
                self.output = Path(filename)
                self._auto_named = True
        
        self.name = self.output.name
        self._temp_root = temp_root
        self._config = config
        self._progress_callback = progress_callback

        self.total: Optional[int] = None
        self.downloaded = 0
        self.speed_bps = 0.0
        self.status = "queued"
        self.error: Optional[str] = None

        self._lock = asyncio.Lock()
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_event = asyncio.Event()
        self._runner: Optional[asyncio.Task[None]] = None
        self._last_speed_time = time.time()
        self._last_speed_bytes = 0
        self._temp_dir: Optional[Path] = None

    def start(self) -> None:
        if self._runner and not self._runner.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as exc:
            raise RuntimeError("DownloadTask.start() requires a running event loop") from exc
        self._runner = loop.create_task(self._run())

    def pause(self) -> None:
        if self.status == "downloading":
            self._pause_event.clear()
            self._set_status("paused")

    def resume(self) -> None:
        if self.status == "paused":
            self._pause_event.set()
            self._set_status("downloading")

    def stop(self) -> None:
        self._stop_event.set()
        if self.status not in ("completed", "error"):
            self._set_status("stopped")

    def _set_status(self, status: str, error: Optional[str] = None) -> None:
        self.status = status
        self.error = error
        self._notify()

    def _notify(self) -> None:
        if not self._progress_callback:
            return
        update = DownloadProgress(
            task_id=self.id,
            downloaded=self.downloaded,
            total=self.total,
            speed_bps=self.speed_bps,
            status=self.status,
            name=self.name,
            error=self.error,
        )
        self._progress_callback(update)

    async def _update_progress(self, bytes_written: int) -> None:
        async with self._lock:
            self.downloaded += bytes_written
            now = time.time()
            elapsed = now - self._last_speed_time
            if elapsed >= 0.5:
                delta = self.downloaded - self._last_speed_bytes
                self.speed_bps = delta / elapsed if elapsed > 0 else 0.0
                self._last_speed_time = now
                self._last_speed_bytes = self.downloaded
        self._notify()

    async def _wait_if_paused(self) -> None:
        while not self._pause_event.is_set():
            if self._stop_event.is_set():
                return
            await asyncio.sleep(0.1)
        await self._pause_event.wait()

    async def _probe(self, session: aiohttp.ClientSession) -> tuple[Optional[int], bool]:
        """Probe the URL to get file size and check if ranges are supported."""
        try:
            async with session.head(self.url, allow_redirects=True) as response:
                if response.status in range(200, 300):
                    # Try to extract filename from headers if auto-named
                    if self._auto_named:
                        header_filename = _extract_filename_from_headers(dict(response.headers))
                        if header_filename:
                            self.output = Path(self.output.parent, header_filename) if self.output.parent and str(self.output.parent) != '.' else Path(header_filename)
                            self.name = self.output.name
                    
                    size = response.headers.get("Content-Length")
                    accept_ranges = response.headers.get("Accept-Ranges", "")
                    total = int(size) if size else None
                    supports_ranges = accept_ranges.lower() == "bytes"
                    return total, supports_ranges
        except aiohttp.ClientError:
            pass

        try:
            async with session.get(self.url) as response:
                if response.status not in range(200, 300):
                    return None, False
                
                # Try to extract filename from headers if auto-named
                if self._auto_named:
                    header_filename = _extract_filename_from_headers(dict(response.headers))
                    if header_filename:
                        self.output = Path(self.output.parent, header_filename) if self.output.parent and str(self.output.parent) != '.' else Path(header_filename)
                        self.name = self.output.name
                
                size = response.headers.get("Content-Length")
                accept_ranges = response.headers.get("Accept-Ranges", "")
                total = int(size) if size else None
                supports_ranges = accept_ranges.lower() == "bytes"
                return total, supports_ranges
        except aiohttp.ClientError:
            return None, False

    async def _run(self) -> None:
        try:
            self._set_status("downloading")
            timeout = aiohttp.ClientTimeout(
                total=None,
                sock_connect=self._config.timeout,
                sock_read=self._config.timeout,
            )
            connector = aiohttp.TCPConnector(limit=self._config.max_connections)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                self.total, supports_ranges = await self._probe(session)
                if not supports_ranges or not self.total or self._config.parts <= 1:
                    await self._download_single(session)
                else:
                    await self._download_multipart(session, self.total)

            if self._stop_event.is_set():
                await self._cleanup_partial()
                return
            self._set_status("completed")
        except Exception as exc:
            await self._cleanup_partial()
            self._set_status("error", str(exc))

    async def _cleanup_partial(self) -> None:
        try:
            if self.output.exists():
                await asyncio.to_thread(self.output.unlink)
        except OSError:
            pass
        if self._temp_dir:
            await asyncio.to_thread(shutil.rmtree, self._temp_dir, ignore_errors=True)

    async def _download_single(self, session: aiohttp.ClientSession) -> None:
        _ensure_parent(self.output)
        async with session.get(self.url) as response:
            response.raise_for_status()
            async with aiofiles.open(self.output, "wb") as handle:
                async for chunk in response.content.iter_chunked(self._config.chunk_size):
                    if not chunk:
                        continue
                    if self._stop_event.is_set():
                        return
                    await self._wait_if_paused()
                    await handle.write(chunk)
                    await self._update_progress(len(chunk))

    async def _download_range(
        self,
        session: aiohttp.ClientSession,
        start: int,
        end: int,
        path: Path,
        semaphore: asyncio.Semaphore,
    ) -> None:
        headers = {"Range": f"bytes={start}-{end}"}
        async with semaphore:
            async with session.get(self.url, headers=headers) as response:
                if response.status != 206:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message="Range request failed",
                    )
                async with aiofiles.open(path, "wb") as handle:
                    async for chunk in response.content.iter_chunked(self._config.chunk_size):
                        if not chunk:
                            continue
                        if self._stop_event.is_set():
                            return
                        await self._wait_if_paused()
                        await handle.write(chunk)
                        await self._update_progress(len(chunk))

    async def _merge_parts(self, part_paths: list[Path]) -> None:
        _ensure_parent(self.output)
        async with aiofiles.open(self.output, "wb") as target:
            for path in part_paths:
                async with aiofiles.open(path, "rb") as handle:
                    while True:
                        chunk = await handle.read(self._config.chunk_size)
                        if not chunk:
                            break
                        await target.write(chunk)

    async def _download_multipart(self, session: aiohttp.ClientSession, total: int) -> None:
        ranges = compute_ranges(total, self._config.parts)
        temp_dir = self._temp_root / self.id
        self._temp_dir = temp_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
        part_paths = [temp_dir / f"part-{index}.bin" for index in range(len(ranges))]

        max_connections = max(1, min(self._config.max_connections, len(ranges)))
        semaphore = asyncio.Semaphore(max_connections)
        tasks = [
            asyncio.create_task(self._download_range(session, start, end, path, semaphore))
            for (start, end), path in zip(ranges, part_paths)
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        if self._stop_event.is_set():
            await asyncio.to_thread(shutil.rmtree, temp_dir, ignore_errors=True)
            return

        await self._merge_parts(part_paths)
        await asyncio.to_thread(shutil.rmtree, temp_dir, ignore_errors=True)


class DownloadManager:
    def __init__(
        self,
        temp_root: Optional[Path] = None,
        config: Optional[TaskConfig] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> None:
        self._temp_root = temp_root or (Path.home() / ".alter" / "temp")
        self._config = config or TaskConfig()
        self._progress_callback = progress_callback
        self._tasks: dict[str, DownloadTask] = {}

    def add(self, request: DownloadRequest) -> DownloadTask:
        task = DownloadTask(request, self._temp_root, self._config, self._progress_callback)
        self._tasks[task.id] = task
        task._notify()
        return task

    def get(self, task_id: str) -> Optional[DownloadTask]:
        return self._tasks.get(task_id)

    def start(self, task_id: str) -> None:
        task = self.get(task_id)
        if task:
            task.start()

    def pause(self, task_id: str) -> None:
        task = self.get(task_id)
        if task:
            task.pause()

    def resume(self, task_id: str) -> None:
        task = self.get(task_id)
        if task:
            task.resume()

    def stop(self, task_id: str) -> None:
        task = self.get(task_id)
        if task:
            task.stop()

    def list(self) -> list[DownloadTask]:
        return list(self._tasks.values())

    def remove(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)
