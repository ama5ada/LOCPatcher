"""
PatcherApp is the main tkinter application window.

Responsibilities
----------------
- Build and own all tkinter widgets.
- Translate user gestures into worker-thread operations.
- Route thread-safe callbacks from PatcherCore back to the UI via root.after()
- Manage button-enable state through an AppState enum so that adding a new button or operation
    only requires touching the state table.

This module contains no patcher logic, all patch operations are delegated to PatcherCore
"""

import logging
import os
import sys
import subprocess
import threading
from datetime import datetime
from enum import Enum, auto
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk
from typing import Literal, Callable
from core import ActionCancelled, PatcherCore
from config.config import PatcherConfig, CONFIG_PATH
from config.constants import APP_TITLE, LOG_DIR
from utils.logging.log_handler import LogHandler
from utils.network import NetworkClient, build_ssl_context
from utils.utils import find_last_oasis_win32


from theme import (
    FONT_BUTTON,
    FONT_MONO,
    FONT_SMALL,
    FONT_LINK,
    FONT_TITLE,
    PALETTE,
    Tooltip,
    apply_theme
)


class AppButton(Enum):
    CHECK = auto()
    PATCH = auto()
    CANCEL = auto()
    LAUNCH = auto()
    CLEAR = auto()
    CLEAR_LOG = auto()
    EXPORT_LOG = auto()


# Use a state machine for buttons being enabled/disabled
class AppState(Enum):
    IDLE = auto()
    RUNNING = auto()
    NEEDS_PATCH = auto()
    READY_TO_PLAY = auto()


# Button enable/disable based on the current updater state
_BUTTON_STATES: dict[AppState, dict[AppButton, bool]] = {
    AppState.IDLE:          {AppButton.CHECK: True,  AppButton.PATCH: False, AppButton.CANCEL: False,
                             AppButton.LAUNCH: False, AppButton.CLEAR: True},

    AppState.RUNNING:       {AppButton.CHECK: False, AppButton.PATCH: False, AppButton.CANCEL: True,
                             AppButton.LAUNCH: False, AppButton.CLEAR: False},

    AppState.NEEDS_PATCH:   {AppButton.CHECK: True,  AppButton.PATCH: True,  AppButton.CANCEL: False,
                             AppButton.LAUNCH: False, AppButton.CLEAR: True},

    AppState.READY_TO_PLAY: {AppButton.CHECK: True,  AppButton.PATCH: False, AppButton.CANCEL: False,
                             AppButton.LAUNCH: True,  AppButton.CLEAR: True}
}


# Status bar background color keyed by state
_STATUS_BG: dict[AppState, str] = {
    AppState.IDLE: "accent_dim",
    AppState.RUNNING: "sky_dim",
    AppState.NEEDS_PATCH: "orange",
    AppState.READY_TO_PLAY: "green",
}


# Status bar text color
_STATUS_FG: dict[AppState, str] = {
    AppState.IDLE: "text",
    AppState.RUNNING: "text",
    AppState.NEEDS_PATCH: "bg_dark",
    AppState.READY_TO_PLAY: "bg_dark",
}


# Button highlight bar color
_BUTTON_HIGHLIGHT: dict[AppButton, str] = {
    AppButton.CHECK: "sky",
    AppButton.PATCH: "sky",
    AppButton.CANCEL: "orange",
    AppButton.LAUNCH: "green",
    AppButton.CLEAR: "accent"
}


# Border log messages with dashes
def _log_section_header(content: str) -> str:
    return "\u2500\u2500\u2500 " + content + " \u2500\u2500\u2500"


class PatcherApp:
    """
    Main GUI window for the patcher app

    Handles user input and displays information while delegating threaded patching actions to the PatcherCore
    """

    def __init__(self, root: tk.Tk, logger: logging.Logger) -> None:
        self.root = root
        self._log = logger
        self._state = AppState.IDLE
        self.root.title(APP_TITLE)
        self.root.configure(bg=PALETTE["bg_dark"])
        self.root.resizable(False, False)
        self.root.minsize(960, 620)
        self.root.maxsize(960, 620)

        icon_path = os.path.join(os.path.dirname(__file__), "MistServer_101.ico")
        if os.path.isfile(icon_path):
            try:
                # Choosing to ignore typing on this call rather than installing stubs
                self.root.iconbitmap(icon_path) # type: ignore[no-untyped-call]
            except tk.TclError:
                self._log.warning("Failed to set icon on this platform: %s", icon_path)

        apply_theme(root)

        self._cfg = PatcherConfig.load(CONFIG_PATH)
        self._core: PatcherCore | None = None
        self._worker: threading.Thread | None = None
        self._buttons: dict[AppButton, tk.Button] = {}
        self._btn_bars: dict[AppButton, tk.Frame] = {}

        self._build_ui()
        self._apply_state(AppState.IDLE)
        self._refresh_dir_label()

        log_handler = LogHandler(self._cb_log)
        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(logging.Formatter("%(message)s"))

        self._log.addHandler(log_handler)
        self._log.info("Patcher started. Working dir: %s", self._cfg.working_dir)


    # Worker threads so UI doesn't freeze
    def _start_worker(self, target: Callable[[], None]) -> None:
        self._worker = threading.Thread(target=target, daemon=True)
        self._worker.start()


    def _schedule_update(self, callback: Callable[[], None]) -> None:
        self.root.after(0, callback)


    def _build_ui(self) -> None:
        self._build_left_panel()
        self._build_right_panel()

    # Left panel contains most of the buttons and status update
    def _build_left_panel(self) -> None:
        left = tk.Frame(self.root, bg=PALETTE["bg_panel"], width=310, height=620)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        # Title bar
        title_bar = tk.Frame(left, bg=PALETTE["accent_dim"])
        title_bar.pack(fill="x")

        tk.Label(title_bar,
            text="LAST OASIS CLASSIC",
            bg=PALETTE["orange"],
            fg=PALETTE["text"],
            font=FONT_TITLE,
            anchor="center",
            padx=14,
            pady=12
        ).pack(fill="x")

        tk.Frame(left, bg=PALETTE["text"], height=3).pack(fill="x")

        # Game directory
        dir_frame = tk.Frame(left, bg=PALETTE["bg_panel"], pady=10, padx=12)
        dir_frame.pack(fill="x")
        header_row = tk.Frame(dir_frame, bg=PALETTE["bg_panel"])
        header_row.pack(fill="x", pady=(0, 3))
        tk.Label(
            header_row, text="GAME DIRECTORY",
            bg=PALETTE["bg_panel"], fg=PALETTE["text"],
            font=FONT_SMALL, anchor="w",
        ).pack(side="left")

        # Game install detection button
        detect_btn = tk.Button(
            header_row,
            text="detect",
            command=self._on_detect,
            bg=PALETTE["bg_panel"],
            fg=PALETTE["sky"],
            font=FONT_LINK,
            relief="flat",
            bd=0,
            highlightthickness=0,
            activebackground=PALETTE["bg_panel"],
            activeforeground=PALETTE["sky"],
            cursor="hand2",
        )
        detect_btn.pack(side="right")
        Tooltip(detect_btn, "Auto-detect Last Oasis install via Steam registry (Windows only)")

        # Game client presence indicator
        self._exe_indicator = tk.Label(
            header_row, text="",
            bg=PALETTE["bg_panel"],
            font=FONT_SMALL,
        )
        Tooltip(self._exe_indicator, "Indicates whether the current patcher path contains Last Oasis")
        self._exe_indicator.pack(side="left", padx=(0, 6))

        # Directory display box
        dir_border = tk.Frame(dir_frame, bg=PALETTE["border"], padx=1, pady=1)
        dir_border.pack(fill="x")
        dir_inner = tk.Frame(dir_border, bg=PALETTE["bg_widget"])
        dir_inner.pack(fill="x")
        self._dir_label = tk.Label(
            dir_inner, text="",
            bg=PALETTE["bg_widget"], fg=PALETTE["text"],
            font=FONT_SMALL, anchor="w", padx=6, pady=4,
        )
        self._dir_label.pack(side="left", fill="x", expand=True)

        # Button that opens file explorer dialog to select directory
        browse_btn = tk.Button(
            dir_inner, text="[\u2026]",
            command=self._on_browse,
            bg=PALETTE["bg_widget"], fg=PALETTE["text"],
            font=FONT_BUTTON, relief="flat", bd=0, padx=10, pady=4,
            cursor="hand2",
            activebackground=PALETTE["accent_dim"],
            activeforeground=PALETTE["text"],
        )
        browse_btn.pack(side="right")
        Tooltip(browse_btn, "Choose the Last Oasis game folder")

        self._make_divider(left)

        # Action buttons
        btn_frame = tk.Frame(left, bg=PALETTE["bg_panel"], padx=12, pady=6)
        btn_frame.pack(fill="x")
        self._make_button(btn_frame, AppButton.CHECK,  "CHECK FOR UPDATES", self._on_check,
                          "Download patch list and compare with local files",
                          fg_key="text",   active_bg_key="accent_dim")
        self._make_button(btn_frame, AppButton.PATCH,  "PATCH LOC MODS", self._on_patch,
                          "Download all outdated or missing files",
                          fg_key="text",   active_bg_key="accent_dim")
        self._make_button(btn_frame, AppButton.CANCEL, "CANCEL", self._on_cancel,
                          "Cancel the current operation",
                          fg_key="red",      active_bg_key="bg_dark")
        self._make_button(btn_frame, AppButton.LAUNCH,   "LAUNCH GAME", self._on_play,
                          "Start the Last Oasis Classic client",
                          fg_key="green",    active_bg_key="bg_dark")
        self._make_button(btn_frame, AppButton.CLEAR,  "CLEAR LOC MODS", self._on_clear,
                          "Delete all LOC mod files from the game folder",
                          fg_key="accent", active_bg_key="bg_dark")

        self._make_divider(left)

        # Progress section
        prog = tk.Frame(left, bg=PALETTE["bg_panel"], padx=12, pady=8)
        prog.pack(fill="x")

        tk.Label(prog, text="FILE PROGRESS",
                 bg=PALETTE["bg_panel"], fg=PALETTE["text_dim"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        self._step_label = tk.Label(prog, text="\u2014",
                                    bg=PALETTE["bg_panel"], fg=PALETTE["text"],
                                    font=FONT_SMALL, anchor="w",
                                    wraplength=280, justify="left")
        self._step_label.pack(fill="x", pady=(2, 3))
        self._step_bar = ttk.Progressbar(
            prog, orient="horizontal", mode="determinate", length=285,
            style="File.TProgressbar")
        self._step_bar.pack(fill="x", pady=(0, 8))

        tk.Label(prog, text="OVERALL PROGRESS",
                 bg=PALETTE["bg_panel"], fg=PALETTE["text_dim"],
                 font=FONT_SMALL, anchor="w").pack(fill="x")
        self._action_label = tk.Label(prog, text="\u2014",
                                      bg=PALETTE["bg_panel"], fg=PALETTE["text"],
                                      font=FONT_SMALL, anchor="w",
                                      wraplength=280, justify="left")
        self._action_label.pack(fill="x", pady=(2, 3))
        self._action_bar = ttk.Progressbar(
            prog, orient="horizontal", mode="determinate", length=285,
            style="Action.TProgressbar")
        self._action_bar.pack(fill="x")

        # Status strip pinned to the bottom — colour changes with state
        self._status_var = tk.StringVar(value="Please check for updates.")
        self._status_strip = tk.Label(
            left,
            textvariable=self._status_var,
            bg=PALETTE["accent_dim"],
            fg=PALETTE["text"],
            font=FONT_SMALL,
            anchor="w",
            padx=10,
            pady=6,
            wraplength=290,
            justify="left",
        )
        self._status_strip.pack(side="bottom", fill="x")

    # Right panel contains the logger window
    def _build_right_panel(self) -> None:
        right = tk.Frame(self.root, bg=PALETTE["bg_dark"], width=650, height=620, padx=6)
        right.pack(side="left", fill="both", expand=True)
        right.pack_propagate(False)

        # Log header — sky-teal to contrast the warm left panel
        header = tk.Frame(right, bg=PALETTE["sky_dim"], height=32)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="PATCHER LOG",
            bg=PALETTE["sky_dim"], fg=PALETTE["text"],
            font=FONT_SMALL, anchor="w", padx=12,
        ).pack(side="left", fill="y")

        # Log window buttons
        self._make_log_window_button(header, AppButton.EXPORT_LOG, "EXPORT LOG", self._on_export_log, side="right", padx=(4, 0))
        self._make_log_window_button(header, AppButton.CLEAR_LOG, "CLEAR LOG", self._clear_log, side="right")

        tk.Frame(right, bg=PALETTE["sky"], height=2).pack(fill="x")

        # Log text area with border
        container = tk.Frame(right, bg=PALETTE["bg_dark"], pady=6)
        container.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(
            container,
            bg=PALETTE["bg_widget"],
            troughcolor=PALETTE["bg_dark"],
            activebackground=PALETTE["accent_dim"],
            width=10, relief="flat", bd=0,
        )
        scrollbar.pack(side="right", fill="y")

        text_border = tk.Frame(container, bg=PALETTE["border"], padx=1, pady=1)
        text_border.pack(fill="both", expand=True)

        self._log_text = tk.Text(
            text_border,
            state="disabled",
            bg=PALETTE["bg_dark"],
            fg=PALETTE["text"],
            font=FONT_MONO,
            relief="flat",
            bd=0,
            wrap="word",
            yscrollcommand=scrollbar.set,
            cursor="arrow",
            insertbackground=PALETTE["accent"],
            selectbackground=PALETTE["accent_dim"],
            selectforeground=PALETTE["text"],
            spacing1=2,
            spacing3=2
        )

        self._log_text.pack(fill="both", expand=True)
        scrollbar.config(command=self._log_text.yview)

        for tag in ["green","orange", "red", "text_dim", "accent", "sky"]:
            self._log_text.tag_config(tag, foreground=PALETTE[tag])


    # Divider widget
    def _make_divider(self, parent: tk.Frame) -> None:
        """
        Three part divider: dark / border / dark.
        """
        tk.Frame(parent, bg=PALETTE["bg_dark"],  height=1).pack(fill="x")
        tk.Frame(parent, bg=PALETTE["border"],   height=1).pack(fill="x", padx=8)
        tk.Frame(parent, bg=PALETTE["bg_dark"],  height=1).pack(fill="x")


    # Left column buttons that share similar behavior
    def _make_button(self, parent: tk.Frame, key: AppButton, label: str,
        cmd: Callable[[], None], tooltip: str = "", fg_key: str = "accent", active_bg_key: str = "accent_dim") -> tk.Button:

        """
        Full-width button with a 3px left accent bar that helps indicate a button is active
        """
        wrapper = tk.Frame(parent, bg=PALETTE["bg_widget"], pady=2)
        wrapper.pack(fill="x", pady=2)

        accent_bar = tk.Frame(wrapper, bg=PALETTE[_BUTTON_HIGHLIGHT[key]], width=3)
        accent_bar.pack(side="left", fill="y")
        self._btn_bars[key] = accent_bar

        btn = tk.Button(wrapper,
            text=f"  {label}",
            command=cmd,
            bg=PALETTE["bg_widget"],
            fg=PALETTE[fg_key],
            disabledforeground=PALETTE["text_dim"],
            font=FONT_BUTTON,
            relief="flat",
            bd=0,
            pady=8,
            anchor="w",
            cursor="hand2",
            activebackground=PALETTE[active_bg_key],
            activeforeground=PALETTE["text"])

        btn.pack(fill="x")
        self._buttons[key] = btn

        if tooltip:
            Tooltip(btn, tooltip)
        return btn


    def _make_log_window_button(self, parent: tk.Frame, key: AppButton, label: str, cmd: Callable[[], None], side:
        Literal["left", "right", "top", "bottom"] = "right", padx: int | tuple[int, int] = 0) -> tk.Button:

        btn = tk.Button(parent, text=label, command=cmd, bg=PALETTE["sky_dim"], fg=PALETTE["text"], font=FONT_SMALL,
            relief="flat", bd=0, padx=10, pady=0, cursor="hand2", activebackground=PALETTE["bg_widget"],
            activeforeground=PALETTE["text"])

        btn.pack(side=side, padx=padx, fill="y")
        self._buttons[key] = btn

        return btn


    def _apply_state(self, state: AppState) -> None:
        """
        Update buttons to reflect being enabled or disabled based on the action the app is currently taking
        Calls a helper method to actually update the buttons

        :param state: Current state of the app based on user input
        """
        self._state = state
        for key, enabled in _BUTTON_STATES[state].items():
            self._set_button(key, enabled)

        # Update status strip color
        self._status_strip.config(
            bg=PALETTE[_STATUS_BG[state]],
            fg=PALETTE[_STATUS_FG[state]],
        )


    def _set_button(self, key: AppButton, enabled: bool) -> None:
        """
        Helper method that updates individual buttons

        :param key:
        :param enabled:
        """
        btn = self._buttons.get(key)
        bar = self._btn_bars.get(key)
        if btn is None:
            return
        if enabled:
            btn.config(state="normal", cursor="hand2", bg=PALETTE["bg_widget"])
            if bar:
                bar.config(bg=PALETTE[_BUTTON_HIGHLIGHT[key]])
        else:
            btn.config(state="disabled", cursor="arrow", bg=PALETTE["bg_dark"])
            if bar:
                bar.config(bg=PALETTE["bg_widget"])

    # UI update helpers (main thread only)
    def _refresh_dir_label(self) -> None:
        path = self._cfg.working_dir
        display = ("\u2026" + path[-30:]) if len(path) > 32 else path
        self._dir_label.config(text=display)

        # Update exe-present indicator
        exe_path = self._cfg.absolute_exe_path
        exe_present = os.path.isfile(exe_path)
        if exe_present:
            self._exe_indicator.config(text="\u2714", fg=PALETTE["green"])
        else:
            self._exe_indicator.config(text="\u2718", fg=PALETTE["red"])


    def _append_log(self, text: str, tag: str = "") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_text.config(state="normal")
        self._log_text.insert("end", f"[{ts}] ", "text_dim")
        self._log_text.insert("end", text + "\n", tag if tag else "")
        self._log_text.config(state="disabled")
        self._log_text.see("end")

    def _clear_log(self) -> None:
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")

    def _set_status(self, text: str, color: str = "white") -> None:
        self._status_var.set(text)
        if color == "red":
            self._status_strip.config(bg=PALETTE["red"], fg=PALETTE["text"])
        elif color == "orange":
            self._status_strip.config(bg=PALETTE["orange"], fg=PALETTE["bg_dark"])
        elif color == "green":
            self._status_strip.config(bg=PALETTE["green"], fg=PALETTE["bg_dark"])
        else:
            self._status_strip.config(
                bg=PALETTE[_STATUS_BG.get(self._state, "accent_dim")],
                fg=PALETTE[_STATUS_FG.get(self._state, "text")],
            )

    def _set_step_progress(self, value: int, maximum: int, label: str) -> None:
        self._step_bar.config(maximum=max(maximum, 1), value=value)
        self._step_label.config(text=label)

    def _set_action_progress(self, value: int, maximum: int, label: str) -> None:
        self._action_bar.config(maximum=max(maximum, 1), value=value)
        self._action_label.config(text=label)

    # Callbacks so that worker threads can modify UI
    def _cb_status(self, text: str, color: str = "white") -> None:
        self.root.after(0, self._set_status, text, color)

    def _cb_log(self, text: str, tag: str) -> None:
        self.root.after(0, self._append_log, text, tag)

    def _cb_step(self, value: int, maximum: int, label: str) -> None:
        self.root.after(0, self._set_step_progress, value, maximum, label)

    def _cb_action(self, value: int, maximum: int, label: str) -> None:
        self.root.after(0, self._set_action_progress, value, maximum, label)

    # Create the patcher core
    def _build_new_core(self) -> PatcherCore:
        return PatcherCore(
            working_dir=self._cfg.working_dir,
            remote_patch_list=self._cfg.remote_patch_list,
            remote_host=self._cfg.remote_host,
            net=NetworkClient(build_ssl_context()),
            logger=self._log,
            on_status=self._cb_status,
            on_step_progress=self._cb_step,
            on_action_progress=self._cb_action,
            on_patch_list_ready=self._on_patch_list_ready_cb,
            on_files_deleted=self._on_files_deleted_cb,
        )

    # Button action handlers
    def _on_detect(self) -> None:
        """
        Attempt to locate the Last Oasis installation via the Windows registry.

        Falls back gracefully on non-Windows platforms or if the game is not found.
        """
        if sys.platform != "win32":
            messagebox.showinfo(
                "Not supported",
                "Auto-detect is only available on Windows.",
            )
            return

        found = find_last_oasis_win32()

        if found:
            self._cfg.working_dir = os.path.normpath(found)
            self._cfg.save(CONFIG_PATH)
            self._refresh_dir_label()
            self._log.info("Auto-detected game dir: %s", self._cfg.working_dir)
            self._append_log(f"Game directory auto-detected: {self._cfg.working_dir}", "green")
        else:
            messagebox.showwarning(
                "Not found",
                "Could not locate Last Oasis in your Steam libraries.\n\n"
                "Please use the [\u2026] button to set the folder manually.",
            )

    def _on_browse(self) -> None:
        chosen = filedialog.askdirectory(
            title="Select Last Oasis game folder",
            initialdir=self._cfg.working_dir,
        )
        if chosen:
            self._cfg.working_dir = os.path.normpath(chosen)
            self._cfg.save(CONFIG_PATH)
            self._refresh_dir_label()
            self._log.info("Working dir changed: %s", self._cfg.working_dir)
            self._append_log(f"Game directory set: {self._cfg.working_dir}", "accent")

    def _on_check(self) -> None:
        self._apply_state(AppState.RUNNING)
        self._append_log(_log_section_header("Starting patch check"), "accent")
        self._core = self._build_new_core()

        def worker() -> None:
            try:
                if self._core is None:
                    raise RuntimeError("PatcherCore was not initialized")

                ok = self._core.check_for_updates()
                if ok and not self._core.cancelled():
                    self._core.check_local_files()
                    count = len(self._core.outdated_file_list)
                    msg = (f"Check complete \u2014 {count} file(s) need updating." if count
                        else "Check complete \u2014 everything up to date!")
                    next_state = AppState.NEEDS_PATCH if count else AppState.READY_TO_PLAY

                    def update_gui() -> None:
                        self._append_log(msg, "orange" if count else "green")
                        self._apply_state(next_state)

                    self._schedule_update(update_gui)

                else:
                    def update_gui() -> None:
                        self._append_log("Check failed \u2014 see log for details.", "red")
                        self._apply_state(AppState.IDLE)

                    self._schedule_update(update_gui)
            except ActionCancelled:
                def update_gui() -> None:
                    self._cb_status("Check cancelled by user.", "orange")
                    self._apply_state(AppState.IDLE)

                self._schedule_update(update_gui)

        self._start_worker(worker)

    def _on_patch(self) -> None:
        if not self._core or not self._core.outdated_file_list:
            messagebox.showinfo("Nothing to patch", "Run 'Check for Updates' first.")
            return

        self._apply_state(AppState.RUNNING)
        self._append_log(_log_section_header("Starting patch download"), "accent")

        def worker() -> None:
            try:
                if self._core is None:
                    raise RuntimeError("PatcherCore was not initialized")

                ok = self._core.download_new_files()
                msg = ("Patch complete \u2014 all files up to date!" if ok
                        else "Patch finished with errors \u2014 see log.")

                def update_gui() -> None:
                    self._append_log(msg, "green" if ok else "red")
                    self._apply_state(AppState.READY_TO_PLAY if ok else AppState.NEEDS_PATCH)

                self._schedule_update(update_gui)
            except ActionCancelled:
                def update_gui() -> None:
                    self._cb_status("Patch cancelled by user.", "orange")
                    self._apply_state(AppState.IDLE)

                self._schedule_update(update_gui)

        self._start_worker(worker)

    def _on_cancel(self) -> None:
        if self._core:
            self._core.cancel()
            self._append_log("User cancelled current action", "orange")

    def _on_play(self) -> None:
        exe_path = self._cfg.absolute_exe_path
        bin_dir = os.path.normpath(self._cfg.launch_bin_path)
        if not os.path.isfile(exe_path):
            messagebox.showerror(
                "Game not found",
                f"Could not find :\n{exe_path}\n"
                "Please verify your game directory or edit [launcher] in the config file.",
            )
            return
        self._append_log("Launching Last Oasis Classic", "green")
        self._log.info("Launching exe: %s", exe_path)
        try:
            subprocess.Popen(
                [exe_path, "-noeac"],
                cwd=bin_dir,
                shell=False,
            )
        except OSError as exc:
            self._log.error("Launch failed: %s", exc)
            messagebox.showerror("Launch failed", str(exc))

    def _on_clear(self) -> None:
        cache = self._cfg.patch_cache
        if not cache:
            messagebox.showinfo("Nothing to clear",
                                "No LOC mod files are tracked in the patch cache.\n"
                                "Run \'Check for Updates\' first.")
            return
        if not messagebox.askyesno("Clear LOC Mods",
                                   f"This will attempt to delete {len(cache)} tracked LOC mod file(s) "
                                   "from your game folder.\n\nContinue?"):
            return

        self._apply_state(AppState.RUNNING)
        self._append_log(_log_section_header("Clearing LOC mod files"), "accent")

        # Create a patcher core instance that will simply delete all cache files
        core = self._build_new_core()

        # Snapshot the cache at the moment the user confirms
        files_to_clear = list(cache)

        def worker() -> None:
            if core is None:
                raise RuntimeError("PatcherCore was not initialized")

            deleted, missed, errored = core.clear_loc_mods(files_to_clear)
            deleted_msg = f"Cleared {deleted} mod file(s) of {len(files_to_clear)} tracked LOC mod file(s)."
            self._log.info(deleted_msg)
            if missed:
                missed_msg = f"{missed} tracked mod file(s) not found to delete."
                self._log.warning(missed_msg)
            if errored:
                errored_msg = f"Unable to delete {errored} mod file(s)."
                self._log.error(errored_msg)

            def update_gui() -> None:
                self._apply_state(AppState.IDLE)
                self._cb_status("Please check for updates.", "accent_dim")

            self._schedule_update(update_gui)

        self._start_worker(worker)

    def _on_patch_list_ready_cb(self, file_list: list[str]) -> None:
        """
        Persist all files from the patch list into PATCH_CACHE

        :param file_list: List of file names to persist so the patcher knows these files have been modified
        """

        self._cfg.add_to_cache(file_list)
        self._log.debug("PATCH_CACHE updated: %d entries", len(self._cfg.patch_cache))

    def _on_files_deleted_cb(self, deleted: list[str]) -> None:
        """
        Remove successfully-deleted files from PATCH_CACHE

        :param deleted: List of files that were successfully deleted
        """

        self._cfg.remove_from_cache(deleted)

    def _on_export_log(self) -> None:
        content = self._log_text.get("1.0", "end-1c").strip()
        if not content:
            messagebox.showinfo("Empty log", "Nothing to export yet.")
            return
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest_dir = os.path.join(self._cfg.working_dir.rstrip("/"), LOG_DIR)
        os.makedirs(dest_dir, exist_ok=True)
        path = os.path.join(dest_dir, f"session_{ts}.txt")
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            self._append_log(f"Log exported \u2192 {path}", "green")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
