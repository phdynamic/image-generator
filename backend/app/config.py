from pathlib import Path
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Imaginaree"
    DATABASE_URL: str = "sqlite:///./imaginaree.db"
    OUTPUTS_DIR: str = str(PROJECT_ROOT / "outputs" / "images")
    THUMBNAILS_DIR: str = str(PROJECT_ROOT / "outputs" / "thumbnails")
    MODELS_CACHE_DIR: str = str(PROJECT_ROOT / "models_cache")
    DEFAULT_MODEL: str = "Lykon/dreamshaper-8"
    MAX_IMAGE_SIZE: int = 1024
    THUMBNAIL_SIZE: int = 256
    HF_TOKEN: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
