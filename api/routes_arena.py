"""The Model Arena: run every loaded model on the same image and return
directly comparable results. This is the centerpiece endpoint -- see
README > Model families for how to read what comes back, especially the
caption-vs-boxes distinction for the VLM entry.
"""
import io
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

from api.models.base import PredictionResult
from api.models.loader import loader
from api.main_paths import SAMPLES_DIR

router = APIRouter(prefix="/api/arena", tags=["arena"])

ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png"}


class ArenaModelInfo(BaseModel):
    name: str
    family: str
    description: str
    approx_download_mb: int


class ArenaResponse(BaseModel):
    image_width: int
    image_height: int
    results: list[PredictionResult]


@router.get("/models", response_model=list[ArenaModelInfo])
def list_arena_models():
    return [
        ArenaModelInfo(
            name=m.name,
            family=m.family,
            description=m.description,
            approx_download_mb=m.approx_download_mb,
        )
        for m in loader.all()
    ]


@router.post("/compare", response_model=ArenaResponse)
def compare(file: Optional[UploadFile] = File(None), sample_path: Optional[str] = Form(None)):
    """Accepts either an uploaded `file`, or `sample_path` (a path relative
    to data/samples/, e.g. "manufacturing/warehouse_1.jpg") to run against a
    bundled sample image without a browser round-trip. The frontend's
    sample-picker deliberately uses `sample_path` rather than fetching the
    already-displayed <img> and re-uploading it -- mixing a plain <img src>
    load and a fetch() on the same URL made Chrome reuse a cache entry with
    no CORS metadata attached, which fails with a misleading "no
    Access-Control-Allow-Origin header" error even though the server sends
    one. Skipping the client-side re-fetch sidesteps that entirely, and is
    also just less wasteful (no double network transfer)."""
    if not loader.ready:
        raise HTTPException(503, "Models are still loading. Try again shortly.")

    if sample_path:
        resolved = (SAMPLES_DIR / sample_path).resolve()
        if SAMPLES_DIR.resolve() not in resolved.parents or not resolved.is_file():
            raise HTTPException(400, "Invalid sample_path")
        image = Image.open(resolved).convert("RGB")
    elif file is not None:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(400, f"Unsupported file type '{suffix}'. Use one of {sorted(ALLOWED_SUFFIXES)}.")
        data = file.file.read()
        image = Image.open(io.BytesIO(data)).convert("RGB")
    else:
        raise HTTPException(400, "Provide either 'file' or 'sample_path'.")

    results: list[PredictionResult] = [model.predict(image) for model in loader.all()]

    return ArenaResponse(image_width=image.width, image_height=image.height, results=results)
