import io

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from api import webhooks

from .features import extract_features
from .stats import FeatureDriftResult, analyze_feature

router = APIRouter(prefix="/api/drift", tags=["drift"])

MIN_IMAGES_PER_BATCH = 3


def _load_images(files: list[UploadFile]) -> list[Image.Image]:
    images = []
    for f in files:
        data = f.file.read()
        images.append(Image.open(io.BytesIO(data)).convert("RGB"))
    return images


@router.post("/check", response_model=list[FeatureDriftResult])
def check_drift(
    reference: list[UploadFile] = File(..., description="Reference/baseline batch of images"),
    current: list[UploadFile] = File(..., description="Current batch to compare against the reference"),
):
    if len(reference) < MIN_IMAGES_PER_BATCH or len(current) < MIN_IMAGES_PER_BATCH:
        raise HTTPException(
            400,
            f"Each batch needs at least {MIN_IMAGES_PER_BATCH} images to produce a "
            "meaningful distribution -- PSI/KS on 1-2 points isn't informative.",
        )

    reference_images = _load_images(reference)
    current_images = _load_images(current)

    reference_features = [extract_features(img) for img in reference_images]
    current_features = [extract_features(img) for img in current_images]

    feature_names = reference_features[0].keys()
    results = []
    for name in feature_names:
        ref_values = np.array([f[name] for f in reference_features])
        cur_values = np.array([f[name] for f in current_features])
        results.append(analyze_feature(name, ref_values, cur_values))

    significant = [r for r in results if r.verdict == "significant"]
    if significant:
        webhooks.send_event(
            "drift.significant",
            {"features": [r.model_dump() for r in significant]},
        )

    return results
