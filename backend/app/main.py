import os
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
from .routers import generate, gallery, models_router, websocket


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

app.include_router(generate.router)
app.include_router(gallery.router)
app.include_router(models_router.router)
app.include_router(websocket.router)

app.mount("/outputs/images", StaticFiles(directory=settings.OUTPUTS_DIR), name="images")
app.mount("/outputs/thumbnails", StaticFiles(directory=settings.THUMBNAILS_DIR), name="thumbnails")

# Serve built React frontend
if getattr(__import__('sys'), 'frozen', False):
    STATIC_DIR = Path(__import__('sys').executable).parent / "static"
else:
    STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(STATIC_DIR / "index.html"))
