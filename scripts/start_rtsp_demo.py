"""Starts a local RTSP camera simulator for native (non-Docker) development:
MediaMTX as the RTSP server, and one FFmpeg process per scenario looping
that scenario's bundled demo clip into it as a real, continuous RTSP feed
-- three independent feeds (manufacturing, healthcare, video_analytics),
not one feed relabeled three times. This is exactly what docker-compose.yml's
`mediamtx` + `camera-sim-*` services do automatically -- use this script
instead when running the API natively with `uvicorn`.

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
SCENARIOS = {
    "demo-manufacturing": REPO_ROOT / "data" / "samples" / "manufacturing" / "demo_clip.mp4",
    "demo-healthcare": REPO_ROOT / "data" / "samples" / "healthcare" / "demo_clip.mp4",
    "demo-video-analytics": REPO_ROOT / "data" / "samples" / "video_analytics" / "demo_clip.mp4",
}


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
    missing = [str(p) for p in SCENARIOS.values() if not p.exists()]
    if missing:
        sys.exit(f"Demo clip(s) not found: {missing}")

    print(f"Starting mediamtx (RTSP on :{args.rtsp_port}) ...")
    mediamtx_proc = subprocess.Popen([args.mediamtx])
    time.sleep(2)

    ffmpeg_procs = []
    for path_name, clip in SCENARIOS.items():
        rtsp_url = f"rtsp://127.0.0.1:{args.rtsp_port}/{path_name}"
        print(f"Streaming {clip.name} ({clip.parent.name}) into {rtsp_url} (looping) ...")
        ffmpeg_procs.append(
            subprocess.Popen(
                [
                    args.ffmpeg, "-re", "-stream_loop", "-1", "-i", str(clip),
                    "-c", "copy", "-f", "rtsp", rtsp_url,
                ]
            )
        )

    print("\nRTSP demo feeds live:")
    for path_name in SCENARIOS:
        print(f"  rtsp://127.0.0.1:{args.rtsp_port}/{path_name}")
    print("\nThe API's default DEMO_RTSP_URL_* env vars already point at these.")
    print("Press Ctrl+C to stop.\n")

    try:
        for p in ffmpeg_procs:
            p.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for p in ffmpeg_procs:
            p.terminate()
        mediamtx_proc.terminate()


if __name__ == "__main__":
    main()
