"""The transformer side of the comparison: DETR treats detection as a set
prediction problem solved end-to-end by a transformer encoder-decoder --
no anchor boxes, no region proposals, no hand-designed post-processing (in
principle; this implementation still runs a confidence-threshold filter).

Note (`revision="no_timm"`): the default revision of this checkpoint uses a
`timm` backbone loader, which pulls in `pycocotools` as a transitive
dependency -- a package with a real history of failing to build on Windows
without VC++ Build Tools. `no_timm` uses a plain torchvision backbone
instead and avoids that dependency entirely.

`transformers` is pinned to `<5` in requirements.txt because this
checkpoint's published config.json has `dilation: null`, and transformers
5.x's stricter config validation rejects that as a type error rather than
treating it as `false`. This is a real upstream compatibility gap, not
something fixable from this file.
"""
import time

import torch
from transformers import DetrForObjectDetection, DetrImageProcessor

from .base import Detection, PredictionResult


class DetrModel:
    name = "DETR (ResNet-50)"
    family = "transformer"
    description = (
        "Transformer encoder-decoder detector. Frames detection as direct "
        "set prediction instead of proposing regions or using anchor boxes."
    )
    approx_download_mb = 160

    def __init__(self, confidence_threshold: float = 0.7):
        self._processor = DetrImageProcessor.from_pretrained(
            "facebook/detr-resnet-50", revision="no_timm"
        )
        self._model = DetrForObjectDetection.from_pretrained(
            "facebook/detr-resnet-50", revision="no_timm"
        )
        self._model.eval()
        self._confidence_threshold = confidence_threshold

    def predict(self, image) -> PredictionResult:
        width, height = image.size
        inputs = self._processor(images=image, return_tensors="pt")

        start = time.perf_counter()
        with torch.no_grad():
            outputs = self._model(**inputs)
        latency_ms = (time.perf_counter() - start) * 1000

        target_sizes = torch.tensor([[height, width]])
        result = self._processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=self._confidence_threshold
        )[0]

        detections = [
            Detection(
                label=self._model.config.id2label[int(label)],
                confidence=float(score),
                box=tuple(float(v) for v in box),
            )
            for box, label, score in zip(result["boxes"], result["labels"], result["scores"])
        ]

        return PredictionResult(
            model_name=self.name,
            family=self.family,
            latency_ms=latency_ms,
            image_width=width,
            image_height=height,
            detections=detections,
        )
