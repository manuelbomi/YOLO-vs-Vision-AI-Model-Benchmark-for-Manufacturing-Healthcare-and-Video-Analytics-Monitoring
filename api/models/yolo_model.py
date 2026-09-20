"""YOLO family: single-stage, anchor-free real-time detector.

Represents the "YOLO" side of the comparison. YOLO11n is the nano variant --
the smallest/fastest in the family, chosen deliberately so the comparison's
"YOLO is fast" finding isn't an artifact of picking a slow YOLO variant.
"""
import time

from ultralytics import YOLO

from .base import Detection, PredictionResult


class YoloModel:
    name = "YOLO11n"
    family = "yolo"
    description = (
        "Single-stage, anchor-free real-time object detector. Runs the whole "
        "image through one network pass to predict boxes directly."
    )
    approx_download_mb = 6

    def __init__(self, weights: str = "yolo11n.pt", confidence_threshold: float = 0.5):
        self._model = YOLO(weights)
        self._confidence_threshold = confidence_threshold

    def predict(self, image) -> PredictionResult:
        width, height = image.size
        start = time.perf_counter()
        results = self._model(image, conf=self._confidence_threshold, verbose=False)
        latency_ms = (time.perf_counter() - start) * 1000

        detections = []
        result = results[0]
        for box in result.boxes:
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            detections.append(
                Detection(
                    label=self._model.names[int(box.cls)],
                    confidence=float(box.conf),
                    box=(x1, y1, x2, y2),
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
