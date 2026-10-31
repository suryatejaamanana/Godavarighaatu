from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.ratelimit import limiter

settings = get_settings()
settings.validate_for_runtime()  # refuses to start with insecure settings outside development

app = FastAPI(title="Godavari Ghaatu API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
register_error_handlers(app)
if settings.storage_backend == "local":  # development only; production serves from Supabase Storage
    Path(settings.media_root).mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=settings.media_root), name="media")
app.include_router(api_router)
