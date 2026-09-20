"""Interface-compliance smoke tests: does every registered model load and
return a well-formed PredictionResult? This is NOT a detection-accuracy
test (that needs real photographic content -- see the Arena, which is
manually/visually verified against the bundled sample images). This test
exists to catch install/API-breakage regressions (e.g. the transformers 5.x
DETR incompatibility found during development) on every CI run, cheaply,
using a plain synthetic image.
"""
import pytest
from PIL import Image

from api.models.loader import MODEL_CLASSES


@pytest.fixture(scope="module")
def blank_image():
    return Image.new("RGB", (320, 240), color=(128, 128, 128))


@pytest.mark.parametrize("model_cls", MODEL_CLASSES, ids=lambda c: c.__name__)
def test_model_predicts_without_error(model_cls, blank_image):
    model = model_cls()
    result = model.predict(blank_image)

    assert result.model_name == model.name
    assert result.family == model.family
    assert result.latency_ms > 0
    assert result.image_width == 320
    assert result.image_height == 240
    # A blank gray image legitimately has zero objects to detect -- this
    # test checks the *shape* of the output, not detection accuracy (that
    # needs real photographic content; see the Arena for that).
    assert isinstance(result.detections, list)
    if model.family == "vlm":
        assert isinstance(result.caption, str) and result.caption != ""
    else:
        assert result.caption is None
