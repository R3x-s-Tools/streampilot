# -*- mode: python ; coding: utf-8 -*-

datas = []

for optional_file in [".env.example", "README.md"]:
    datas.append((optional_file, "."))

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "obsws_python",
        "openai",
        "requests",
        "websocket",
        "dotenv",
    ],
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
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="DadR3x Command Center",
)

app = BUNDLE(
    coll,
    name="DadR3x Command Center.app",
    icon=None,
    bundle_identifier="tools.r3x.dadr3x-command-center",
)
