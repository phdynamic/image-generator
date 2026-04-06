import sys
import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _get_app_root() -> Path:
    """Get the app root directory, works both in dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle — exe is in dist/Imaginaree/
        return Path(sys.executable).parent
    else:
        # Running in development — backend/ is the parent
        return Path(__file__).resolve().parent.parent.parent


APP_ROOT = _get_app_root()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Imaginaree"
    DATABASE_URL: str = f"sqlite:///{APP_ROOT / 'imaginaree.db'}"
    OUTPUTS_DIR: str = str(APP_ROOT / "outputs" / "images")
    THUMBNAILS_DIR: str = str(APP_ROOT / "outputs" / "thumbnails")
    MODELS_CACHE_DIR: str = str(APP_ROOT / "models_cache")
    DEFAULT_MODEL: str = "Lykon/dreamshaper-8"
    MAX_IMAGE_SIZE: int = 1024
    THUMBNAIL_SIZE: int = 256
    HF_TOKEN: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure output directories exist
os.makedirs(settings.OUTPUTS_DIR, exist_ok=True)
os.makedirs(settings.THUMBNAILS_DIR, exist_ok=True)
os.makedirs(settings.MODELS_CACHE_DIR, exist_ok=True)
