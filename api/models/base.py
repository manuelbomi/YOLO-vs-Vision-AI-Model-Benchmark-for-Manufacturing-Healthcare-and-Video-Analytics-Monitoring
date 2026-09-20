"""The plug-in interface every model wrapper implements.

Adding a new model to the benchmark means writing one class that satisfies
this interface and registering it in api/models/registry_loader.py -- no
other code needs to change. See README.md > Extensibility.
"""
from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel

ModelFamily = Literal["yolo", "cnn", "transformer", "vlm"]


class Detection(BaseModel):
    """One detected object. `box` is (x1, y1, x2, y2) in pixel coordinates."""

    label: str
    confidence: float
    box: tuple[float, float, float, float]


class PredictionResult(BaseModel):
    model_name: str
    family: ModelFamily
    latency_ms: float
    image_width: int
    image_height: int
    detections: list[Detection] = []
    # Set instead of (or alongside) detections for models whose native output
    # isn't bounding boxes, e.g. an image caption. Never silently coerced
    # into fake boxes -- see README's "comparing unlike outputs" note.
    caption: str | None = None


class VisionModel(Protocol):
    name: str
    family: ModelFamily
    description: str
    approx_download_mb: int

    def predict(self, image) -> PredictionResult:
        """image is a PIL.Image.Image in RGB mode."""
        ...
