"""Registers the 4 benchmarked models in the registry with real measured
metrics, so the Model Registry dashboard has something to show on a fresh
clone instead of an empty table. Run this once against a running API:

    python scripts/seed_registry.py [--api-base http://localhost:8000]

Measures each model's actual latency on this machine (via api.models.loader,
in-process -- no need for the API to expose a benchmarking endpoint) rather
than hardcoding numbers, so the seeded metrics are always true for whatever
hardware you're running on.
"""
import argparse
import sys
import time
from pathlib import Path

import httpx
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.models.loader import MODEL_CLASSES  # noqa: E402

SAMPLE_IMAGE = Path(__file__).resolve().parents[1] / "data" / "samples" / "manufacturing" / "warehouse_1.jpg"


def measure_latency_ms(model, image, n=3) -> float:
    times = []
    for _ in range(n):
        result = model.predict(image)
        times.append(result.latency_ms)
    return sum(times) / len(times)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://localhost:8000")
    args = parser.parse_args()

    image = Image.open(SAMPLE_IMAGE).convert("RGB")

    for cls in MODEL_CLASSES:
        print(f"Loading {cls.__name__} ...")
        model = cls()
        avg_latency = measure_latency_ms(model, image)
        print(f"  measured latency: {avg_latency:.1f} ms (avg of 3 runs)")

        framework = {
            "yolo": "ultralytics",
            "segmentation": "ultralytics",
            "cnn": "torchvision",
        }.get(model.family, "transformers")
        task_type = {
            "vlm": "image-captioning",
            "segmentation": "instance-segmentation",
        }.get(model.family, "object-detection")
        payload = {
            "name": model.name,
            "version": "1.0.0",
            "family": model.family,
            "framework": framework,
            "task_type": task_type,
            "approx_download_mb": model.approx_download_mb,
            "metrics": {"latency_ms": round(avg_latency, 1)},
        }
        response = httpx.post(f"{args.api_base}/api/registry/models", json=payload, timeout=10)
        response.raise_for_status()
        print(f"  registered as model id {response.json()['id']}\n")


if __name__ == "__main__":
    main()
