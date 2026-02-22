from pathlib import Path
import sys
import os

project_root = Path(os.getcwd())
assets_dir = project_root / "assets"

if sys.platform == "darwin":
    icon_file = assets_dir / "MistServer_101.icns"
else:
    icon_file = assets_dir / "MistServer_101.ico"

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(icon_file), "./assets/"),
    ],
    hiddenimports=["winreg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LOCPatcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(icon_file),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LOCPatcher",
)