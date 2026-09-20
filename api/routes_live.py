"""The Live Monitor: run a chosen model on a live video source and stream
the annotated result to the browser as MJPEG (multipart/x-mixed-replace)
-- the same mechanism most IP cameras use for their own browser preview,
so no WebSocket/WebRTC plumbing is needed just to *watch* a stream. See
README > Networking protocols for where this fits next to RTSP/WebRTC/
webhooks, and api/ingestion/webrtc.py for the browser-source alternative.

Three named demo sources are available, one per scenario -- each is a real
RTSP feed (MediaMTX + FFmpeg looping that scenario's sample clip; see
scripts/start_rtsp_demo.py and the mediamtx/camera-sim-* Docker services),
not a shared feed relabeled three times.
"""
import io
import os
import time

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw

from api.ingestion.video_source import FrameSource
from api.models.loader import loader

router = APIRouter(prefix="/api/live", tags=["live"])

DEMO_SOURCES = {
    "manufacturing": {
        "url": os.environ.get("DEMO_RTSP_URL_MANUFACTURING", "rtsp://127.0.0.1:8554/demo-manufacturing"),
        "description": (
            "Manufacturing demo: a looping RTSP feed built from "
            "data/samples/manufacturing/demo_clip.mp4."
        ),
    },
    "healthcare": {
        "url": os.environ.get("DEMO_RTSP_URL_HEALTHCARE", "rtsp://127.0.0.1:8554/demo-healthcare"),
        "description": (
            "Healthcare demo (staged PPE/training imagery, no real patients): "
            "a looping RTSP feed built from data/samples/healthcare/demo_clip.mp4."
        ),
    },
    "video_analytics": {
        "url": os.environ.get("DEMO_RTSP_URL_VIDEO_ANALYTICS", "rtsp://127.0.0.1:8554/demo-video-analytics"),
        "description": (
            "Video analytics demo: a looping RTSP feed built from "
            "data/samples/video_analytics/demo_clip.mp4."
        ),
    },
}
MAX_INFERENCE_FPS = 6.0  # deliberately capped -- see FrameSource.frames() docstring


def _draw_overlay(image: Image.Image, result, fps: float) -> Image.Image:
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for det in result.detections:
        x1, y1, x2, y2 = det.box
        draw.rectangle([x1, y1, x2, y2], outline=(0, 220, 90), width=3)
        label = f"{det.label} {det.confidence:.2f}"
        draw.rectangle([x1, y1 - 16, x1 + 8 * len(label), y1], fill=(0, 220, 90))
        draw.text((x1 + 2, y1 - 15), label, fill=(0, 0, 0))

    banner = f"{result.model_name} | {fps:.1f} fps | {result.latency_ms:.0f} ms/frame"
    if result.caption:
        banner += f" | \"{result.caption}\""
    draw.rectangle([0, 0, annotated.width, 22], fill=(0, 0, 0))
    draw.text((6, 4), banner, fill=(255, 255, 255))
    return annotated


def _mjpeg_generator(model_name: str, source: str):
    model = loader.get(model_name)
    if model is None:
        raise HTTPException(404, f"Unknown model '{model_name}'")

    frame_source = FrameSource(source).open()
    try:
        last_tick = time.monotonic()
        for frame in frame_source.frames(max_fps=MAX_INFERENCE_FPS):
            result = model.predict(frame)
            now = time.monotonic()
            fps = 1.0 / max(now - last_tick, 1e-6)
            last_tick = now

            annotated = _draw_overlay(frame, result, fps)
            buffer = io.BytesIO()
            annotated.save(buffer, format="JPEG", quality=80)
            jpeg_bytes = buffer.getvalue()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
            )
    finally:
        frame_source.close()


def _resolve_source(source: str) -> str:
    if source in DEMO_SOURCES:
        return DEMO_SOURCES[source]["url"]
    return source  # treat anything else as a literal RTSP URL


@router.get("/stream")
def live_stream(
    model: str = Query(..., description="Exact model name, e.g. 'YOLO11n'"),
    source: str = Query(
        default="manufacturing",
        description="One of 'manufacturing' | 'healthcare' | 'video_analytics', or any RTSP URL",
    ),
):
    return StreamingResponse(
        _mjpeg_generator(model, _resolve_source(source)),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/sources")
def list_sources():
    return DEMO_SOURCES
