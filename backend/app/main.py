from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
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
