import subprocess
import sys

def build():
    args = [
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--name", "LOCPatcher",
        "--onedir",
        "--windowed",
        "--icon", "assets/MistServer_101.ico",
        "--add-data", "assets/MistServer_101.ico;.",
        "--clean",
        "-y"
    ]

    subprocess.run(args, check=True)

if __name__ == "__main__":
    build()