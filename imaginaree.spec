# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Paths
backend_dir = os.path.join(os.getcwd(), 'backend')
static_dir = os.path.join(backend_dir, 'static')
icon_path = os.path.join(os.getcwd(), 'star.ico')

a = Analysis(
    ['run_app.py'],
    pathex=[backend_dir],
    binaries=[],
    datas=[
        (static_dir, 'static'),
        (icon_path, '.'),
    ],
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
