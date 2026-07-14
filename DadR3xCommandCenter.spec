# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import platform
import certifi
project_root = Path.cwd()

datas = [(certifi.where(), "certifi"),]
for optional_file in [".env.example", "README.md", "CHANGELOG.md"]:
    optional_path = project_root / optional_file
    if optional_path.exists():
        datas.append((str(optional_path), "."))

icon_path = None
if platform.system() == "Darwin" and (project_root / "assets" / "icon.icns").exists():
    icon_path = str(project_root / "assets" / "icon.icns")
elif platform.system() == "Windows" and (project_root / "assets" / "icon.ico").exists():
    icon_path = str(project_root / "assets" / "icon.ico")

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "obsws_python",
    "openai",
    "requests",
    "websocket",
    "dotenv",
    "certifi",
]

a = Analysis(
    ["app.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "black", "ruff", "tests"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DadR3x Command Center",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_path,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="DadR3x Command Center",
)

if platform.system() == "Darwin":
    app = BUNDLE(
        coll,
        name="DadR3x Command Center.app",
        icon=icon_path,
        bundle_identifier="tools.r3x.dadr3x-command-center",
        info_plist={
            "CFBundleName": "DadR3x Command Center",
            "CFBundleDisplayName": "DadR3x Command Center",
            "CFBundleIdentifier": "tools.r3x.dadr3x-command-center",
            "CFBundleShortVersionString": "0.2.1",
            "CFBundleVersion": "0.2.1",
            "NSHighResolutionCapable": True,
        },
    )
