import subprocess
import sys

def build():
    args = [
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--name", "LOCPatcher",
        "--onedir",
        "--windowed",
        "--icon", "MistServer_101.ico",
        "--add-data", "MistServer_101.ico;.",
        "--clean",
    ]

    subprocess.run(args, check=True)

if __name__ == "__main__":
    build()