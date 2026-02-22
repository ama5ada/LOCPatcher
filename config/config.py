import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_data_dir

from config.constants import (
    APP_AUTHOR,
    APP_NAME
)


# Windows defaults
_DEFAULT_BIN_DIR  = "Mist/Binaries/Win64"
_DEFAULT_EXE_NAME = "MistClient-Win64-Shipping.exe"


# Patcher .ini file location
def _default_config_path() -> Path:
    data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "loc_patcher.ini"


CONFIG_PATH: Path = _default_config_path()


@dataclass
class PatcherConfig:
    """
    All user-configurable or persisted patcher settings.

    Attributes
    ----------
    working_dir:
        Absolute path to the game root folder (trailing slash normalised on load).

    launch_bin_dir:
        Relative path from working_dir to the folder containing the game executable
        Defaults to the Windows binary path

    launch_exe_name:
        Filename of the executable to launch.  Must live inside launch_bin_dir

    patch_cache:
        Ordered list of relative file paths that the patcher has written to working_dir.
        Used by the patcher to know which files to remove to uninstall the mods
    """

    working_dir: str = field(default_factory=os.getcwd)
    launch_bin_dir: str  = _DEFAULT_BIN_DIR
    launch_exe_name: str = _DEFAULT_EXE_NAME
    patch_cache: list[str] = field(default_factory=list)


    @property
    def launch_bin_path(self) -> str:
        """Absolute path to the directory that contains the game executable."""
        return os.path.join(self.working_dir, self.launch_bin_dir)


    @property
    def absolute_exe_path(self) -> str:
        """Absolute path to the game executable."""
        return os.path.join(self.launch_bin_path, self.launch_exe_name)


    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "PatcherConfig":
        """
        Load config from path, falling back to defaults for any missing key
        """
        cfg = configparser.ConfigParser()
        defaults = cls()

        if os.path.isfile(path):
            try:
                cfg.read(path, encoding="utf-8")
            except configparser.Error:
                pass

        patcher_section = cfg["patcher"]  if cfg.has_section("patcher")  else {}

        working_dir = patcher_section.get("working_dir", defaults.working_dir)
        working_dir = os.path.normpath(working_dir)

        # Parse PATCH_CACHE from a newline separated list of file names, empty string -> empty list
        cache_section = cfg["patch_cache"] if cfg.has_section("patch_cache") else {}
        raw_files = cache_section.get("files", "")
        patch_cache = [f.strip() for f in raw_files.splitlines() if f.strip()]

        return cls(
            working_dir = working_dir,
            launch_bin_dir = patcher_section.get("bin_dir", defaults.launch_bin_dir),
            launch_exe_name = patcher_section.get("exe_name", defaults.launch_exe_name),
            patch_cache = patch_cache,
        )


    def save(self, path: Path = CONFIG_PATH) -> None:
        """
        Persist the current settings to the ini file
        Creates the file if it doesn't exist already
        """
        cfg = configparser.ConfigParser()
        cfg["patcher"] = {
            "working_dir": self.working_dir,
            "bin_dir": self.launch_bin_dir,
            "exe_name": self.launch_exe_name
        }
        cfg["patch_cache"] = {
            "files": "\n".join(self.patch_cache),
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            cfg.write(fh)


    def add_to_cache(self, files: list[str]) -> None:
        """
        Add files to the cache so that clearing mods will delete all mod files that were downloaded even if some no
        longer exist in the patch list the client receives.
        """
        existing = set(self.patch_cache)
        for f in files:
            if f not in existing:
                self.patch_cache.append(f)
                existing.add(f)
        self.save()


    def remove_from_cache(self, files: list[str]) -> None:
        """
        Remove files from the cache when they've been deleted successfully
        """
        to_remove = set(files)
        self.patch_cache = [f for f in self.patch_cache if f not in to_remove]
        self.save()