"""Segmentation: same YOLO11 family as the detector, but the "instance
segmentation" head -- it predicts a pixel-accurate mask per object instead
of just a box. Included as a 5th, distinct comparison point: the other 4
models all answer "where is a rough rectangle around this object," which
is often not what a real inspection task needs (e.g. measuring the exact
area of a corrosion patch or a defect needs its actual outline, not a box
that also covers background pixels).
"""
import time

from ultralytics import YOLO

from .base import Detection, PredictionResult


class YoloSegModel:
    name = "YOLO11n-seg"
    family = "segmentation"
    description = (
        "Same single-stage YOLO11 architecture, with an added mask head: "
        "predicts a pixel-accurate polygon outline per object, not just a "
        "bounding box."
    )
    approx_download_mb = 7

    def __init__(self, weights: str = "yolo11n-seg.pt", confidence_threshold: float = 0.5):
        self._model = YOLO(weights)
        self._confidence_threshold = confidence_threshold

    def predict(self, image) -> PredictionResult:
        width, height = image.size
        start = time.perf_counter()
        results = self._model(image, conf=self._confidence_threshold, verbose=False)
        latency_ms = (time.perf_counter() - start) * 1000

        detections = []
        result = results[0]
        # `masks.xy` is already rescaled to the original image's pixel
        # coordinates, in the same order as `boxes` -- no separate
        # coordinate mapping needed. A blank/no-detection image has
        # `result.masks is None`, not an empty list.
        polygons = result.masks.xy if result.masks is not None else []
        for box, polygon in zip(result.boxes, polygons):
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            detections.append(
                Detection(
                    label=self._model.names[int(box.cls)],
                    confidence=float(box.conf),
                    box=(x1, y1, x2, y2),
                    mask=[(float(x), float(y)) for x, y in polygon],
                )
            )

        return PredictionResult(
            model_name=self.name,
            family=self.family,
            latency_ms=latency_ms,
            image_width=width,
            image_height=height,
            detections=detections,
        )
