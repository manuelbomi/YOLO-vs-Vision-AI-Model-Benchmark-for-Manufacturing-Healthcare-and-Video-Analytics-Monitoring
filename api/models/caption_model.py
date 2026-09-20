"""The small vision-language-model side of the comparison.

Unlike the three detectors above, this model doesn't predict bounding
boxes at all -- it describes the whole scene in natural language, the way a
small multimodal assistant would. That's a genuinely different output type,
and the Arena UI shows it as a caption panel rather than forcing it into
fake boxes. See README > "Comparing unlike outputs" for why that's the
honest way to present this comparison, and > "Why not a larger/newer VLM"
for what was tried first (Moondream2) and why this was swapped in instead
during implementation: Moondream2's only cleanly `transformers`-loadable
revision is ~3.7GB+ (not the small quantized build its own announcement
blog describes), which didn't fit this project's "clone and run without a
multi-GB download" goal. BLIP has no `trust_remote_code` requirement either,
which is one less supply-chain trust decision for anyone deploying this.
"""
import time

from transformers import BlipForConditionalGeneration, BlipProcessor

from .base import PredictionResult


class CaptionModel:
    name = "BLIP (image captioning)"
    family = "vlm"
    description = (
        "Small vision-language model. Describes the whole scene in a "
        "sentence instead of predicting per-object boxes -- included to "
        "compare latency/resource cost against the detectors, not box "
        "accuracy, since the output type is genuinely different."
    )
    approx_download_mb = 990

    def __init__(self):
        self._processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self._model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        self._model.eval()

    def predict(self, image) -> PredictionResult:
        width, height = image.size
        inputs = self._processor(image, return_tensors="pt")

        start = time.perf_counter()
        output_ids = self._model.generate(**inputs, max_new_tokens=30)
        latency_ms = (time.perf_counter() - start) * 1000

        caption = self._processor.decode(output_ids[0], skip_special_tokens=True)

        return PredictionResult(
            model_name=self.name,
            family=self.family,
            latency_ms=latency_ms,
            image_width=width,
            image_height=height,
            detections=[],
            caption=caption,
        )
