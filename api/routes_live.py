"""The Live Monitor: run a chosen model on a live video source (by default
the bundled RTSP demo feed) and stream the annotated result to the browser
as MJPEG (multipart/x-mixed-replace) -- the same mechanism most IP cameras
use for their own browser preview, so no WebSocket/WebRTC plumbing is
needed just to *watch* a stream. See README > Networking protocols for
where this fits next to RTSP/WebRTC/webhooks, and api/ingestion/webrtc.py
for the browser-source alternative.
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

DEFAULT_RTSP_URL = os.environ.get("DEMO_RTSP_URL", "rtsp://127.0.0.1:8554/demo")
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


@router.get("/stream")
def live_stream(
    model: str = Query(..., description="Exact model name, e.g. 'YOLO11n'"),
    source: str = Query(default="demo", description="'demo' for the bundled RTSP feed, or any RTSP URL"),
):
    resolved_source = DEFAULT_RTSP_URL if source == "demo" else source
    return StreamingResponse(
        _mjpeg_generator(model, resolved_source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/sources")
def list_sources():
    return {
        "demo": {
            "url": DEFAULT_RTSP_URL,
            "description": (
                "Bundled manufacturing demo: a looping RTSP feed built from "
                "data/samples/manufacturing/demo_clip.mp4 by MediaMTX + "
                "FFmpeg. See scripts/start_rtsp_demo.py."
            ),
        }
    }
