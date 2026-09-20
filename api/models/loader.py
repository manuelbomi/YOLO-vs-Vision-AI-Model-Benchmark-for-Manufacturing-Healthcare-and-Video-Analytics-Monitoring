"""Loads every model exactly once and hands out the cached instances.

To add a new model to the benchmark: write a class satisfying
api.models.base.VisionModel, add one line to MODEL_CLASSES below, and
nothing else needs to change -- the Arena endpoint, the registry seed
script, and the frontend all iterate over whatever this loader exposes.
"""
from .base import VisionModel
from .caption_model import CaptionModel
from .detr_model import DetrModel
from .fasterrcnn_model import FasterRCNNModel
from .yolo_model import YoloModel

MODEL_CLASSES: list[type[VisionModel]] = [
    YoloModel,
    FasterRCNNModel,
    DetrModel,
    CaptionModel,
]


class ModelLoader:
    def __init__(self):
        self._models: dict[str, VisionModel] = {}

    def load_all(self):
        for cls in MODEL_CLASSES:
            instance = cls()
            self._models[instance.name] = instance

    @property
    def ready(self) -> bool:
        return len(self._models) == len(MODEL_CLASSES)

    def all(self) -> list[VisionModel]:
        return list(self._models.values())

    def get(self, name: str) -> VisionModel | None:
        return self._models.get(name)


loader = ModelLoader()
