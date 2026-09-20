"""FastAPI backend for the Vision Model Benchmark platform.

Run from the repo root (so `api`, `data`, and the registry DB path all
resolve):
    uvicorn api.main:app --reload --port 8000
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.drift.routes import router as drift_router
from api.models.loader import loader
from api.registry.db import init_db
from api.registry.routes import router as registry_router
from api.routes_arena import router as arena_router

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = REPO_ROOT / "data" / "samples"

app = FastAPI(title="Vision Model Benchmark API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

if SAMPLES_DIR.exists():
    app.mount("/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")

app.include_router(arena_router)
app.include_router(registry_router)
app.include_router(drift_router)


@app.on_event("startup")
def _startup():
    init_db()
    loader.load_all()


@app.get("/api/health")
def health():
    return {"status": "ok", "models_ready": loader.ready, "models_loaded": len(loader.all())}
