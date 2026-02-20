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


# Helper method that identifies the Last Oasis install on a machine
def find_last_oasis_win32() -> str | None:
    """
    Return the Last Oasis game folder path, or None if not found.

    1. Read the Steam install path from the Windows registry
    2. Enumerate all Steam library folders from libraryfolders.vdf
    3. In each library, check for the manifest file for app 903950 (Last Oasis)
        return the steamapps/common/Last Oasis path if it exists on disk.
    """
    import winreg

    STEAM_APP_ID = "903950"
    GAME_FOLDER_NAME = "Last Oasis"

    # Registry locations Steam uses (64-bit and 32-bit views)
    REG_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Valve\Steam"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Valve\Steam"),
    ]

    steam_path: str | None = None
    for hive, subkey in REG_PATHS:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
                break
        except OSError:
            continue

    if not steam_path or not os.path.isdir(steam_path):
        return None

    # Collect all library roots from libraryfolders.vdf
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    library_roots: list[str] = [steam_path]

    if os.path.isfile(vdf_path):
        try:
            with open(vdf_path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    # VDF lines look like:  "path"    "E:\\SteamLibrary"
                    tokens = [t for t in line.split('"') if t.strip()]
                    if len(tokens) >= 2 and tokens[0].strip().lower() == "path":
                        lib = tokens[1].strip()
                        if os.path.isdir(lib) and lib not in library_roots:
                            library_roots.append(lib)
        except OSError:
            pass


    # Search each library for the game
    for lib in library_roots:
        manifest = os.path.join(lib, "steamapps", f"appmanifest_{STEAM_APP_ID}.acf")
        if os.path.isfile(manifest):
            game_dir = os.path.join(lib, "steamapps", "common", GAME_FOLDER_NAME)
            if os.path.isdir(game_dir):
                return game_dir

    return None