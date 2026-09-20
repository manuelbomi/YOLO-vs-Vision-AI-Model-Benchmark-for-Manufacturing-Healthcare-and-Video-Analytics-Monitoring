"""Browser camera -> this backend, over WebRTC -- the second of the two
"video in" protocols this repo demonstrates for real (RTSP is the other;
see video_source.py). Follows the same pattern as aiortc's own
`examples/server` reference implementation: the browser opens an
RTCPeerConnection, sends an SDP offer over a plain HTTP POST (no signaling
server needed beyond this one endpoint), and this backend answers with a
peer connection that reads the browser's video track, runs it through a
chosen model, and sends the annotated video back on an outgoing track.

No TURN server is configured -- fine for same-machine/LAN demo use (a
public STUN server is enough), not for browsers behind restrictive NATs on
different networks. See README > Networking protocols for that tradeoff
and why RTSP remains the more common choice for fixed industrial cameras
specifically.
"""
from __future__ import annotations

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from aiortc.mediastreams import VideoStreamTrack
from av import VideoFrame
from PIL import ImageDraw

from api.models.loader import loader

from api.models.loader import loader

relay = MediaRelay()
_peer_connections: set[RTCPeerConnection] = set()


class AnnotatedVideoTrack(VideoStreamTrack):
    """Wraps an incoming track; each frame is run through `model_name` and
    returned with detection boxes (or a caption banner) drawn on it."""

    def __init__(self, source_track, model_name: str):
        super().__init__()
        self.source_track = source_track
        self.model_name = model_name

    async def recv(self):
        frame = await self.source_track.recv()

        model = loader.get(self.model_name)
        image = frame.to_image()  # PyAV VideoFrame -> PIL Image
        annotated = image

        if model is not None:
            result = model.predict(image)
            annotated = image.copy()
            draw = ImageDraw.Draw(annotated)
            for det in result.detections:
                x1, y1, x2, y2 = det.box
                draw.rectangle([x1, y1, x2, y2], outline=(0, 220, 90), width=3)
                draw.text((x1 + 2, max(y1 - 14, 0)), det.label, fill=(0, 220, 90))
            banner = f"{result.model_name} | {result.latency_ms:.0f} ms/frame"
            if result.caption:
                banner += f' | "{result.caption}"'
            draw.rectangle([0, 0, annotated.width, 20], fill=(0, 0, 0))
            draw.text((4, 3), banner, fill=(255, 255, 255))

        new_frame = VideoFrame.from_image(annotated)
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame


async def handle_offer(sdp: str, sdp_type: str, model_name: str) -> RTCSessionDescription:
    pc = RTCPeerConnection()
    _peer_connections.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in ("failed", "closed", "disconnected"):
            _peer_connections.discard(pc)
            await pc.close()

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            pc.addTrack(AnnotatedVideoTrack(relay.subscribe(track), model_name))

    offer = RTCSessionDescription(sdp=sdp, type=sdp_type)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return pc.localDescription


async def close_all_connections():
    for pc in list(_peer_connections):
        await pc.close()
    _peer_connections.clear()
