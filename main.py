"""
    Application entry, set up logger and GUI
"""

import tkinter as tk

from utils.logging.logger import setup_logging
from app import PatcherApp

def main() -> None:
    logger = setup_logging()
    root = tk.Tk()
    PatcherApp(root, logger)
    root.mainloop()


if __name__ == "__main__":
    main()
