"""The "other CNN" side of the comparison: a two-stage, region-proposal
detector -- a genuinely different detection paradigm from YOLO's single
forward pass. Faster R-CNN first proposes candidate regions, then classifies
and refines each one, which is why it's typically slower but was historically
more accurate before single-stage detectors closed the gap.
"""
import time

import torch
from torchvision.models.detection import (
    FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
    fasterrcnn_mobilenet_v3_large_320_fpn,
)

from .base import Detection, PredictionResult


class FasterRCNNModel:
    name = "Faster R-CNN (MobileNetV3)"
    family = "cnn"
    description = (
        "Two-stage region-proposal CNN detector: first proposes candidate "
        "regions, then classifies and refines each one. Slower than "
        "single-stage detectors but a different, historically influential "
        "design."
    )
    approx_download_mb = 74

    def __init__(self, confidence_threshold: float = 0.5):
        weights = FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT
        self._model = fasterrcnn_mobilenet_v3_large_320_fpn(
            weights=weights, box_score_thresh=confidence_threshold
        )
        self._model.eval()
        self._preprocess = weights.transforms()
        self._labels = weights.meta["categories"]

    def predict(self, image) -> PredictionResult:
        width, height = image.size
        import torchvision.transforms.functional as F

        tensor = F.pil_to_tensor(image)
        batch = [self._preprocess(tensor)]

        start = time.perf_counter()
        with torch.no_grad():
            output = self._model(batch)[0]
        latency_ms = (time.perf_counter() - start) * 1000

        detections = [
            Detection(
                label=self._labels[label],
                confidence=float(score),
                box=tuple(float(v) for v in box),
            )
            for box, label, score in zip(output["boxes"], output["labels"], output["scores"])
        ]

        return PredictionResult(
            model_name=self.name,
            family=self.family,
            latency_ms=latency_ms,
            image_width=width,
            image_height=height,
            detections=detections,
        )
