"""A single abstraction over "give me frames" regardless of where they come
from -- a local video file, a webcam, or an RTSP camera. All three are the
exact same `cv2.VideoCapture(source)` call; RTSP just needs a
`rtsp://...` URL instead of a file path or webcam index. This is precisely
why RTSP is the practical default for camera ingestion in this kind of
system (see README > Networking protocols) -- there's no separate client
library to integrate, OpenCV already speaks it.
"""
from __future__ import annotations

import time
from typing import Iterator

import cv2
from PIL import Image


class FrameSource:
    def __init__(self, source: str | int):
        self.source = source
        self._cap: cv2.VideoCapture | None = None

    def open(self):
        self._cap = cv2.VideoCapture(self.source)
        if not self._cap.isOpened():
            raise IOError(f"Could not open video source: {self.source}")
        return self

    def frames(self, max_fps: float | None = None) -> Iterator[Image.Image]:
        """Yields frames as PIL Images. If max_fps is set, sleeps between
        reads to avoid pulling frames faster than needed (a live-monitor
        overlay doesn't need to run inference at the source's native frame
        rate, and often shouldn't -- see README > Live Monitor)."""
        if self._cap is None:
            self.open()
        min_interval = (1.0 / max_fps) if max_fps else 0.0
        last_yield = 0.0
        while True:
            ret, frame_bgr = self._cap.read()
            if not ret:
                break
            now = time.monotonic()
            remaining = min_interval - (now - last_yield)
            if remaining > 0:
                time.sleep(remaining)  # also prevents a tight cv2.read() spin loop
            last_yield = time.monotonic()
            yield Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))

    def close(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None
