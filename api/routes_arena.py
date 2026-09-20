"""The Model Arena: run every loaded model on the same image and return
directly comparable results. This is the centerpiece endpoint -- see
README > Model families for how to read what comes back, especially the
caption-vs-boxes distinction for the VLM entry.
"""
import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

from api.models.base import PredictionResult
from api.models.loader import loader

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
def compare(file: UploadFile = File(...)):
    if not loader.ready:
        raise HTTPException(503, "Models are still loading. Try again shortly.")

    from pathlib import Path

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type '{suffix}'. Use one of {sorted(ALLOWED_SUFFIXES)}.")

    data = file.file.read()
    image = Image.open(io.BytesIO(data)).convert("RGB")

    results: list[PredictionResult] = [model.predict(image) for model in loader.all()]

    return ArenaResponse(image_width=image.width, image_height=image.height, results=results)
