"""Starts a local RTSP camera simulator for native (non-Docker) development:
MediaMTX as the RTSP server, and FFmpeg looping the bundled manufacturing
demo clip into it as a real, continuous RTSP feed. This is exactly what
docker-compose.yml's `mediamtx` + `camera-sim` services do automatically --
use this script instead when running the API natively with `uvicorn`.

Requires `mediamtx` and `ffmpeg` on PATH (or pass their paths explicitly).
MediaMTX: https://github.com/bluenviron/mediamtx/releases (single binary,
no install). FFmpeg: `winget install Gyan.FFmpeg` / `apt install ffmpeg` /
`brew install ffmpeg`.
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CLIP = REPO_ROOT / "data" / "samples" / "manufacturing" / "demo_clip.mp4"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mediamtx", default="mediamtx", help="Path to the mediamtx executable")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="Path to the ffmpeg executable")
    parser.add_argument("--rtsp-port", type=int, default=8554)
    args = parser.parse_args()

    if shutil.which(args.mediamtx) is None:
        sys.exit(f"mediamtx not found on PATH ('{args.mediamtx}'). See this script's docstring.")
    if shutil.which(args.ffmpeg) is None:
        sys.exit(f"ffmpeg not found on PATH ('{args.ffmpeg}'). See this script's docstring.")
    if not DEMO_CLIP.exists():
        sys.exit(f"Demo clip not found at {DEMO_CLIP}")

    print(f"Starting mediamtx (RTSP on :{args.rtsp_port}) ...")
    mediamtx_proc = subprocess.Popen([args.mediamtx])
    time.sleep(2)

    rtsp_url = f"rtsp://127.0.0.1:{args.rtsp_port}/demo"
    print(f"Streaming {DEMO_CLIP.name} into {rtsp_url} (looping) ...")
    ffmpeg_proc = subprocess.Popen(
        [
            args.ffmpeg, "-re", "-stream_loop", "-1", "-i", str(DEMO_CLIP),
            "-c", "copy", "-f", "rtsp", rtsp_url,
        ]
    )

    print(f"\nRTSP demo feed live at {rtsp_url}")
    print("Point the API at it with DEMO_RTSP_URL (already the default) and start the Live Monitor.")
    print("Press Ctrl+C to stop.\n")

    try:
        ffmpeg_proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        ffmpeg_proc.terminate()
        mediamtx_proc.terminate()


if __name__ == "__main__":
    main()
