import subprocess
import sys


def build() -> None:
    subprocess.run([sys.executable, "-m", "PyInstaller", "LOCPatcher.spec", "-y"])

if __name__ == "__main__":
    build()