"""
Visual constants, ttk style configuration, Tooltip helper widget
"""
import tkinter
import tkinter as tk
from tkinter import ttk
from typing import Optional

PALETTE: dict[str, str] = {
    # Backgrounds - brown
    "bg_dark":    "#120c06",     # near-black
    "bg_panel":   "#1c1108",     # dark wood
    "bg_widget":  "#2a1c0e",     # mid brown

    # Borders
    "border":     "#3a2410",     # amber

    # Accent - gold
    "accent":     "#c8962a",     # gold
    "accent_dim": "#6e4e12",     # shadowed gold

    # Text - white
    "text":       "#e8dcc0",     # bright readable
    "text_dim":   "#8c7248",     # shadowed

    # Status colors
    "green":      "#4a9e6e",     # sage
    "orange":     "#c87828",     # orange - warnings
    "red":        "#b83220",     # red - errors / failures
    "sky":        "#3a8898",     # blue
    "sky_dim":    "#1e4e58",     # shadowed blue
}

# Fonts definitions
FONT_TITLE  = ("Courier New", 13, "bold")
FONT_SMALL  = ("Courier New", 8)
FONT_LINK   = ("Courier New", 8, "underline")
FONT_BUTTON = ("Courier New", 9, "bold")
FONT_MONO   = ("Courier New", 8)


def apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")

    # Copy the layout from the base progressbar and inherit with the custom progress bars
    base_layout = style.layout("Horizontal.TProgressbar")
    style.layout("File.TProgressbar", base_layout)
    style.layout("Action.TProgressbar", base_layout)

    # Step progress bar - gold
    style.configure(
        "File.TProgressbar",
        troughcolor=PALETTE["bg_widget"],
        background=PALETTE["accent"],
        bordercolor=PALETTE["border"],
        lightcolor=PALETTE["accent"],
        darkcolor=PALETTE["accent_dim"],
        thickness=8,
    )

    # Action progress bar - blue
    style.configure(
        "Action.TProgressbar",
        troughcolor=PALETTE["bg_widget"],
        background=PALETTE["sky"],
        bordercolor=PALETTE["border"],
        lightcolor=PALETTE["sky"],
        darkcolor=PALETTE["sky_dim"],
        thickness=8,
    )


# Tooltip
class Tooltip:
    """
    Hover tooltip for widgets

    Usage :
        Tooltip(my_button, "Explanation of button function")
    """

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self._widget = widget
        self._text = text
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event: Optional[tkinter.Event]=None) -> None:
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self._tip,
            text=self._text,
            bg=PALETTE["bg_widget"],
            fg=PALETTE["text"],
            font=FONT_SMALL,
            relief="flat",
            bd=1,
            padx=6,
            pady=3,
        ).pack()

    def _hide(self, _event: Optional[tkinter.Event]=None) -> None:
        if self._tip:
            self._tip.destroy()
            self._tip = None