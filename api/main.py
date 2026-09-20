"""FastAPI backend for the Vision Model Benchmark platform.

Run from the repo root (so `api`, `data`, and the registry DB path all
resolve):
    uvicorn api.main:app --reload --port 8000
"""
import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.drift.routes import router as drift_router
from api.main_paths import SAMPLES_DIR
from api.models.loader import loader
from api.registry.db import init_db
from api.registry.routes import router as registry_router
from api.routes_arena import router as arena_router
from api.routes_live import router as live_router
from api.routes_webhooks import router as webhooks_router
from api.routes_webrtc import router as webrtc_router
from api.webhooks_worker import run_forever as run_webhook_retry_worker

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
app.include_router(live_router)
app.include_router(webhooks_router)
app.include_router(webrtc_router)


_webhook_worker_task: asyncio.Task | None = None


@app.on_event("startup")
async def _startup():
    global _webhook_worker_task
    init_db()
    loader.load_all()
    _webhook_worker_task = asyncio.create_task(run_webhook_retry_worker())


@app.on_event("shutdown")
async def _shutdown():
    if _webhook_worker_task:
        _webhook_worker_task.cancel()


@app.get("/api/health")
def health():
    return {"status": "ok", "models_ready": loader.ready, "models_loaded": len(loader.all())}
