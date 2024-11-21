# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

# Path to the browsers.json file
fake_useragent_data_path = os.path.join(
    'venv', 'Lib', 'site-packages', 'fake_useragent', 'data', 'browsers.json'
)

# Analyze the application
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    # Include GIF files, scraper.py, and browsers.json in the datas
    datas=[
        ('gif/loading.gif', 'gif'),
        ('gif/success.gif', 'gif'),
        ('gif/failure.gif', 'gif'),
        ('scraper.py', '.'),
        (fake_useragent_data_path, 'fake_useragent/data')  # Include the browsers.json file
    ],
    hiddenimports=[
        'webdriver_manager.chrome',  # Example of hidden import
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)

# Create the executable
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Data Scraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect everything into the final application directory
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Data Scraper',
)
