# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(SPEC)), '..', 'src'))

block_cipher = None

a = Analysis(
    ['../src/metaeditor_safetensors/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
        'PIL.Image',
        'numpy',
        'metaeditor_safetensors.commands',
        'metaeditor_safetensors.commands.base',
        'metaeditor_safetensors.commands.browse_file',
        'metaeditor_safetensors.commands.load_metadata',
        'metaeditor_safetensors.commands.save',
        'metaeditor_safetensors.commands.set_thumbnail',
        'metaeditor_safetensors.commands.view_thumbnail',
        'metaeditor_safetensors.commands.toggle_raw',
        'metaeditor_safetensors.commands.show_about',
    ],
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
    name='MetaEditor-SafeTensors',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
