# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Awake macOS app

block_cipher = None

a = Analysis(
    ['menubar.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['rumps'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Awake',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

app = BUNDLE(
    exe,
    name='Awake.app',
    icon=None,
    bundle_identifier='com.pysuite.awake',
    info_plist={
        'LSUIElement': True,  # Hide from Dock
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1',
        'NSHumanReadableCopyright': 'Copyright © 2025 PySuite. All rights reserved.',
    },
)
