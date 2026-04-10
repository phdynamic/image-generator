import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .database import engine, Base
from .services.model_manager import ModelManager
from .services.generator import ImageGenerator
from .routers import generate, gallery, models_router, websocket, upscale, prompts

logger = logging.getLogger(__name__)


def _get_static_dir() -> Path | None:
    candidates = []
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        # PyInstaller 6.x puts datas in _internal/ subdirectory
        candidates.append(exe_dir / "_internal" / "static")
        candidates.append(exe_dir / "static")
        # sys._MEIPASS is the runtime temp dir where onefile extracts
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.append(Path(meipass) / "static")
    else:
        candidates.append(Path(__file__).resolve().parent.parent / "static")

    for d in candidates:
        if d.exists() and (d / "index.html").exists():
            logger.info(f"Serving frontend from: {d}")
            return d
    logger.warning(f"Frontend static dir not found. Checked: {[str(c) for c in candidates]}")
    return None


STATIC_DIR = _get_static_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    model_manager = ModelManager()
    generator = ImageGenerator(model_manager)
    app.state.model_manager = model_manager
    app.state.generator = generator
    yield


app = FastAPI(title="Imaginaree API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes first — these take priority
app.include_router(generate.router)
app.include_router(gallery.router)
app.include_router(models_router.router)
app.include_router(websocket.router)
app.include_router(upscale.router)
app.include_router(prompts.router)

# Output file mounts
app.mount("/outputs/images", StaticFiles(directory=settings.OUTPUTS_DIR), name="images")
app.mount("/outputs/thumbnails", StaticFiles(directory=settings.THUMBNAILS_DIR), name="thumbnails")

# Serve built React frontend — mount the whole static dir as a fallback
if STATIC_DIR is not None:
    # This must be last — it catches everything not matched above
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
