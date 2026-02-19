import tkinter as tk

from logger import setup_logging
from app import PatcherApp

"""
    Application entry, set up logger and GUI
"""

def main() -> None:
    logger = setup_logging()
    root = tk.Tk()
    PatcherApp(root, logger)
    root.mainloop()


if __name__ == "__main__":
    main()
