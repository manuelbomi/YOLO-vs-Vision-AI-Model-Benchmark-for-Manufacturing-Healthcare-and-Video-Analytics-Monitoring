"""Turns an image into the small, inspectable numeric features the drift
demo monitors. Deliberately simple (brightness, contrast, saturation) so
the resulting drift numbers are easy to sanity-check against what the
images actually look like -- not a learned embedding, which would be more
sensitive but much harder to explain in a README.
"""
import numpy as np
from PIL import Image


def extract_features(image: Image.Image) -> dict[str, float]:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    hsv = np.asarray(image.convert("HSV"), dtype=np.float32)

    brightness = rgb.mean()
    contrast = rgb.std()
    saturation = hsv[:, :, 1].mean()

    return {
        "brightness": float(brightness),
        "contrast": float(contrast),
        "saturation": float(saturation),
    }
