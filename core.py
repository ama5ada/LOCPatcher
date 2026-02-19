import logging
import os
import shutil
import tempfile
import threading
import time
import urllib.error
from typing import Callable
from urllib.parse import urlparse
from network import NetworkClient

from constants import (
    DOWNLOAD_CHUNK,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
)

from utils import (
    compute_crc32,
    convert_file_size,
    format_eta,
    is_safe_path,
)

# Exception used when a user clicks the cancel button
class ActionCancelled(Exception):
    pass

class PatcherCore:
    """
    Handles actual patching workflow:

    1. check_patch_list - fetch and parse the remote manifest
    2. check_local_files - compare local files against the manifest
    3. download_new_files - download every outdated or missing file

    All progress and status updates to the UI are executed through callbacks so the updates are thread safe
    """

    def __init__(self, working_dir: str, remote_patch_list: str, remote_host: str, net: NetworkClient, logger: logging.Logger,
        on_status: Callable[[str, str], None],
        on_step_progress: Callable[[int, int, str], None],
        on_action_progress: Callable[[int, int, str], None],
        on_patch_list_ready: Callable[[list], None] | None = None,
        on_files_deleted: Callable[[list], None] | None = None,
    ) -> None:
        self.working_dir = os.path.normpath(working_dir)
        self.remote_patch_list = remote_patch_list
        self.remote_host = remote_host
        self._net = net
        self._log = logger
        self._on_status = on_status
        self._on_step = on_step_progress
        self._on_action = on_action_progress
        self._on_patch_list_ready = on_patch_list_ready
        self._on_files_deleted = on_files_deleted

        self.updated_file_map: dict[str, dict] = {}
        self.outdated_file_list: list[str] = []
        self._cancel_event = threading.Event()


    def cancel(self) -> None:
        self._cancel_event.set()


    def cancelled(self) -> bool:
        return self._cancel_event.is_set()


    def _check_cancelled(self) -> None:
        if self.cancelled():
            raise ActionCancelled()


    def check_for_updates(self) -> bool:
        parsed = urlparse(self.remote_patch_list)
        short_url = parsed.netloc + parsed.path

        self._on_status(f"Fetching patch list from {short_url}", "white")
        self._on_action(0, 3, "Step 1/3 — Fetching patch list")
        self._log.info("Fetching patch list: %s", self.remote_patch_list)

        try:
            content = self._net.fetch_text(self.remote_patch_list)

            self._check_cancelled()

            self.updated_file_map = self._parse_patch_list(content)

            count = len(self.updated_file_map)

            self._log.info("Patch list loaded: %d files", count)
            self._on_status(f"Patch list OK — {count} files tracked", "green")
            self._on_action(1, 3, "Step 1/3 — Patch list fetched")

            # Notify caller so it can persist all known file paths to PATCH_CACHE
            if self._on_patch_list_ready:
                self._on_patch_list_ready(list(self.updated_file_map.keys()))

            return True

        except urllib.error.HTTPError as exc:
            self._on_status(f"ERROR: HTTP {exc.code} — {exc.reason}", "red")
            return False

        except urllib.error.URLError as exc:
            self._on_status(f"ERROR: Network — {exc.reason}", "red")
            return False

        except ActionCancelled:
            raise

        except Exception as exc:
            self._log.exception("Unexpected error fetching patch list")
            self._on_status(f"ERROR: {exc}", "red")
            return False


    def _parse_patch_list(self, content: str) -> dict[str, dict]:
        """
        Parse the patch manifest text into a file-map dict.

        Expected line format::

            <relative/path> <CRC32_HEX> <byte_size>

        Malformed lines are logged and skipped.
        """
        file_map: dict[str, dict] = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 3:
                self._log.warning("Malformed patch list line: %r", line)
                continue
            path, file_hash, size_str = parts
            try:
                file_map[path] = {"hash": file_hash, "size": int(size_str)}
            except ValueError:
                self._log.warning("Invalid size in patch list line: %r", line)
        return file_map


    def check_local_files(self) -> None:
        """
        Compare local files against ``updated_file_map``.

        Populates ``self.outdated_file_list`` with every path that is
        missing locally or whose size/CRC does not match the manifest.
        """

        self._check_cancelled()

        total = len(self.updated_file_map)
        self._on_status("Checking local files…", "white")
        self._on_action(1, 3, "Step 2/3 — Checking local files")
        self._log.info("Scanning %d paths under: %s", total, self.working_dir)

        present: list[str] = []
        self.outdated_file_list = []

        for idx, key in enumerate(self.updated_file_map, start=1):
            self._check_cancelled()

            self._on_step(idx, total, f"Scanning {idx}/{total}: {key.split('/')[-1]}")
            if os.path.isfile(os.path.join(self.working_dir, key)):
                present.append(key)
            else:
                self._log.debug("Missing: %s", key)
                self.outdated_file_list.append(key)

        self._on_action(2, 3, "Step 2/3 — Local scan complete")
        self._validate_files(present)


    def _validate_files(self, candidates: list[str]) -> None:
        """
        CRC-check every file in *candidates*, adding failures to the outdated list.
        """
        self._check_cancelled()

        total = len(candidates)
        self._on_status("Validating local files (CRC)…", "white")
        self._on_action(2, 3, "Step 3/3 — Validating checksums")
        self._log.info("Validating %d existing files", total)

        for idx, key in enumerate(candidates, start=1):
            self._check_cancelled()

            self._on_step(idx, total, f"Validating {idx}/{total} : \n{key.split('/')[-1]}")
            try:
                if not self._validate_file(key):
                    self._log.info("Outdated: %s", key)
                    self.outdated_file_list.append(key)
            except OSError as exc:
                self._log.warning("Could not validate %s: %s", key, exc)
                self.outdated_file_list.append(key)

        count = len(self.outdated_file_list)
        if count:
            self._on_status(f"Found {count} outdated/missing file(s) — patch required.", "orange")
        else:
            self._on_status("All files up to date. Ready to play!", "green")
        self._on_action(3, 3, "Step 3/3 — Validation complete")


    def _validate_file(self, key: str) -> bool:
        """
        Make sure the file matches what is expected (not malformed in transit)

        :param key: Name of file
        :return: True/False if the file CRC matches the patch list
        """
        entry = self.updated_file_map[key]
        local_path = os.path.join(self.working_dir, key)

        local_size = os.stat(local_path).st_size
        if local_size != entry["size"]:
            self._log.debug(
                "Size mismatch %s: local=%d remote=%d", key, local_size, entry["size"]
            )
            return False

        local_crc = compute_crc32(local_path)
        remote_crc = entry["hash"].upper()
        if local_crc != remote_crc:
            self._log.debug(
                "CRC mismatch %s: local=%s remote=%s", key, local_crc, remote_crc
            )
            return False

        return True


    def _cancellable_sleep(self, seconds: float, interval: float = 0.1) -> None:
        """
        Sleep function that can be interrupted by a cancel action

        :param seconds: Amount of time to sleep for
        :param interval: Amount of time actually slept between each check for a cancellation
        :return:
        """
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self.cancelled():
                raise ActionCancelled()
            time.sleep(interval)


    def download_new_files(self) -> bool:
        """
        Download every file in outdated_file_list with retry

        :return: True/False if all files were downloaded successfully.
        :raises ActionCancelled: if cancelled while processing files
        """
        total_files = len(self.outdated_file_list)
        if total_files == 0:
            return True

        total_bytes = sum(self.updated_file_map[f]["size"] for f in self.outdated_file_list)
        downloaded_bytes = 0
        total_tracker = _SpeedTracker()
        all_ok = True

        self._on_status(f"Downloading {total_files} file(s) — {convert_file_size(total_bytes)} total", "white")
        self._log.info("Starting download: %d files, %s total", total_files, convert_file_size(total_bytes))

        for file_idx, key in enumerate(self.outdated_file_list, start=1):
            self._check_cancelled()

            file_name = key.split("/")[-1]
            success = False

            for attempt in range(1, MAX_RETRIES + 1):
                self._check_cancelled()

                back_off = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                attempt_suffix = f" (attempt {attempt})" if attempt > 1 else ""
                self._on_status(f"[{file_idx}/{total_files}] {file_name}{attempt_suffix}", "white")

                try:
                    written = self._download_file(key, downloaded_bytes, total_bytes, file_idx, total_files, total_tracker)
                    if self._validate_file(key):
                        downloaded_bytes += written
                        self._log.info("Downloaded OK: %s", key)
                        success = True
                        break
                    self._log.warning("Validation failed after download: %s (attempt %d)", key, attempt)
                    if attempt < MAX_RETRIES:
                        self._on_status(f"Validation failed for {file_name}, retrying in {back_off:.0f}s…", "orange")
                        self._cancellable_sleep(back_off)

                except (urllib.error.URLError, OSError) as exc:
                    self._log.warning("Download error %s (attempt %d): %s", key, attempt, exc)
                    if attempt < MAX_RETRIES:
                        self._on_status(f"Error downloading {file_name}, retrying in {back_off:.0f}s…", "orange")
                        self._cancellable_sleep(back_off)

            if not success:
                self._log.error("FAILED to download %s after %d attempts", key, MAX_RETRIES)
                self._on_status(f"FAILED: {file_name} — see logs for details", "red")
                all_ok = False

        if all_ok and not self.cancelled():
            self._on_status("Patch complete. Ready to play!", "green")
        return all_ok

    def _download_file(self, key: str, already_downloaded: int, total_bytes: int, file_idx: int,
                       total_files: int, total_tracker) -> int:
        """
        Download the file to a temp path, rename it into place

        :return: the number of bytes written

        :raises ValueError: on a directory-traversal attempt
        :raises ActionCancelled: if cancelled mid-stream
        """
        dest_path = os.path.normpath(os.path.join(self.working_dir, key))
        if not is_safe_path(self.working_dir, dest_path):
            raise ValueError(f"Directory traversal blocked: {key}")

        url = self.remote_host + key
        expected = self.updated_file_map[key]["size"]
        file_name = key.split("/")[-1]

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(dest_path))
        try:
            with self._net.stream_binary(url) as resp, os.fdopen(tmp_fd, "wb") as out:
                tmp_fd = None
                written = 0
                speed_tracker = _SpeedTracker()

                while True:
                    self._check_cancelled()
                    chunk = resp.read(DOWNLOAD_CHUNK)
                    if not chunk:
                        break
                    out.write(chunk)
                    written += len(chunk)

                    speed_bps = speed_tracker.update(written)

                    # Per-file progress
                    pct = written / expected if expected else 0
                    eta_sec = (expected - written) / speed_bps if speed_bps > 0 else float("inf")
                    self._on_step(
                        written, expected,
                        f"{file_name}\n"
                        f"{convert_file_size(written):<10} / {convert_file_size(expected)} ({pct:.0%})\n"
                        f"{convert_file_size(int(speed_bps)) + '/s':<13}"
                        f"ETA {format_eta(eta_sec)}"
                    )

                    # Overall progress
                    overall = already_downloaded + written
                    total_bps = total_tracker.update(overall)

                    total_pct = overall / total_bytes if total_bytes else 0
                    total_eta = (total_bytes - overall) / total_bps if total_bps > 0 else float("inf")
                    self._on_action(
                        overall, total_bytes,
                        f"Downloading File {file_idx}/{total_files} — \n"
                        f"{convert_file_size(overall):<10} / {convert_file_size(total_bytes)} "
                        f"({total_pct:.0%})\n"
                        f"{convert_file_size(int(total_bps)) + '/s':<13}"
                        f"ETA {format_eta(total_eta)}",
                    )

            shutil.move(tmp_path, dest_path)
            tmp_path = None
            return written
        finally:
            if tmp_fd is not None:
                try:
                    os.close(tmp_fd)
                except OSError:
                    pass
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


    def clear_loc_mods(self, file_list: list[str]) -> tuple[int, int, int]:
        """
        Delete every file in file_list that exists in working_dir

        Skips paths that would escape the working directory

        Removes files that were successfully deleted from the patch cache

        :param file_list: List of files to delete (Patch Cache)
        :return tuple[int, int, int]:
        """
        deleted = 0
        missed = 0
        error = 0
        successfully_removed: list[str] = []

        for rel_path in file_list:
            abs_path = os.path.normpath(os.path.join(self.working_dir, rel_path))
            if not is_safe_path(self.working_dir, abs_path):
                self._log.error("Skipping unsafe path: %s", rel_path)
                error += 1
                continue
            if os.path.isfile(abs_path):
                try:
                    os.remove(abs_path)
                    self._log.info("Deleted: %s", rel_path)
                    self._on_status(f"Deleted {rel_path.split('/')[-1]}", "white")
                    deleted += 1
                    successfully_removed.append(rel_path)
                except OSError as exc:
                    error += 1
                    self._log.error("Could not delete %s: %s", rel_path, exc)
                    self._on_status(f"ERROR deleting {rel_path.split('/')[-1]}: {exc}", "red")
            else:
                # File already absent - still remove from cache
                missed += 1
                self._log.debug("File not found : %s", rel_path)
                successfully_removed.append(rel_path)

        if successfully_removed and self._on_files_deleted:
            self._on_files_deleted(successfully_removed)

        return deleted, missed, error


class _SpeedTracker:
    """
    Rolling bandwidth estimator helper class

    Each download creates an instance which knows when the download began and when an update should occur
    """

    def __init__(self, updated_interval: float = 0.5) -> None:
        self._updated_interval = updated_interval
        self._start = time.monotonic()
        self._last_time = self._start
        self._speed: float = 0.0

    def update(self, total_written: int) -> float:
        """
        Bandwidth estimate method that updates based on the bytes downloaded so far

        :param total_written: Number of bytes downloaded so far
        :return: Speed estimate of file download over entire download lifetime
        """
        now = time.monotonic()
        elapsed = now - self._last_time
        if elapsed >= self._updated_interval:
            self._speed = total_written / (now - self._start)
            self._last_time = now
        return self._speed