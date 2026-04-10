# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

block_cipher = None

# Paths
backend_dir = os.path.join(os.getcwd(), 'backend')
static_dir = os.path.join(backend_dir, 'static')
icon_path = os.path.join(os.getcwd(), 'star.ico')

# Packages whose metadata diffusers/transformers check at runtime
metadata_packages = [
    'requests',
    'filelock',
    'numpy',
    'packaging',
    'pyyaml',
    'regex',
    'tokenizers',
    'safetensors',
    'huggingface-hub',
    'transformers',
    'diffusers',
    'importlib_metadata',
    'tqdm',
    'Pillow',
]

datas = [
    (static_dir, 'static'),
    (icon_path, '.'),
]

for pkg in metadata_packages:
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

# Collect data files from packages that ship config files
for pkg in ['diffusers', 'transformers', 'huggingface_hub']:
    try:
        datas += collect_data_files(pkg)
    except Exception:
        pass

# Also include the .py source files from diffusers and transformers so
# that runtime source-code inspection (e.g. experts implementation checks)
# works inside the frozen bundle.
for pkg in ['diffusers', 'transformers']:
    try:
        datas += collect_data_files(pkg, include_py_files=True)
    except Exception:
        pass

a = Analysis(
    ['run_app.py'],
    pathex=[backend_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'app',
        'app.main',
        'app.config',
        'app.database',
        'app.models',
        'app.models.image',
        'app.routers',
        'app.routers.generate',
        'app.routers.gallery',
        'app.routers.models_router',
        'app.routers.websocket',
        'app.routers.upscale',
        'app.routers.prompts',
        'app.services',
        'app.services.model_manager',
        'app.services.generator',
        'app.services.upscaler',
        'app.utils',
        'app.utils.image_utils',
        'app.utils.gpu_utils',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'diffusers',
        'transformers',
        'torch',
        'accelerate',
        'safetensors',
        'huggingface_hub',
        'requests',
        'filelock',
        'tqdm',
        'regex',
        'tokenizers',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'pydantic',
        'pydantic_settings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['webview', 'pywebview'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Imaginaree',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No terminal window
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Imaginaree',
)
