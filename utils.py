import math
import os
import sys
import zlib
from pathlib import Path


def convert_file_size(size_in_bytes: int) -> str:
    """
    Converts bytes into the largest logical unit, handles invalid sizes

    :param size_in_bytes:
    :return: String representation of size in bytes with the largest logical unit
    """
    if size_in_bytes == 0:
        return "0 B"
    if not isinstance(size_in_bytes, (int, float)) or size_in_bytes < 0:
        return "NaN"
    labels = ["B", "KB", "MB", "GB", "TB"]
    idx = min(int(math.floor(math.log(size_in_bytes, 1024))), len(labels) - 1)
    value = round(size_in_bytes / math.pow(1024, idx), 2)
    return f"{value} {labels[idx]}"


def format_eta(seconds: float) -> str:
    """
    Convert a duration in seconds to a timer string

    :param seconds:
    :return: '--:--' for invalid values or HH:MM:SS string
    """
    if seconds < 0 or not math.isfinite(seconds):
        return "--:--"

    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)

    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    if m:
        return f"{m:02d}:{s:02d}"
    return f":{s:02d}"


def is_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Return True if target_path resolves to a location inside base_dir

    Blocks directory-traversal tricks
    """
    base = Path(base_dir).resolve()
    target = Path(target_path).resolve()
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def compute_crc32(filepath: str) -> str:
    """
    Return the CRC-32 checksum of a file

    Reads in 64 KB blocks to manage memory usage for large files
    """
    crc = 0
    with open(filepath, "rb", 65536) as fh:
        while chunk := fh.read(65536):
            crc = zlib.crc32(chunk, crc)
    return "%08X" % (crc & 0xFFFFFFFF)


def resource_path(relative_path: str) -> str:
    """
    Resolve a path relative to the application root

    Works correctly both when running from source and when frozen by PyInstaller
    (temporary data is unpacked into sys._MEIPASS)
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
