# Vision Model Benchmark — Frontend

A React + TypeScript app for the [Vision Model Benchmark API](../README.md):
five dashboards over one FastAPI backend.

| Tab | What it does |
|---|---|
| **Model Arena** | Run all 4 models (YOLO, Faster R-CNN, DETR, BLIP) on the same image, side by side, with bounding boxes drawn directly on the image and a latency comparison table |
| **Live Monitor** | Watch a chosen model run live on a bundled RTSP demo feed (manufacturing, healthcare, or video-analytics), streamed back as annotated MJPEG |
| **Webcam (WebRTC)** | Your browser's camera, streamed to the backend over WebRTC, annotated, and streamed back — no RTSP involved |
| **Drift Monitor** | Upload a reference batch and a current batch of images; see Population Stability Index / KS-test / Cohen's d results, plus webhook config and durable delivery history |
| **Model Registry** | The SQLite-backed model-governance table: promote/archive model versions |

## Running

The [API](../api/README.md) must be running first (from the repo root):

```bash
uvicorn api.main:app --reload --port 8000
```

For the Live Monitor tab, also start the RTSP demo feed (see the main
[README's Quickstart](../README.md#quickstart)):

```bash
python scripts/start_rtsp_demo.py
```

Then, in this directory:

```bash
npm install
npm run dev
```

Open the URL Vite prints (typically http://localhost:5173).

## Configuring the API URL

Defaults to `http://localhost:8000`. To point at a different host/port,
create `.env.local`:

```bash
cp .env.example .env.local
# edit VITE_API_BASE_URL in .env.local
```

Restart `npm run dev` after changing it — Vite only reads `.env*` files at
startup.

## A note on the Model Arena's sample picker

Clicking a bundled sample image calls `/api/arena/compare` with a
`sample_path` form field instead of fetching the already-displayed
`<img>` and re-uploading it as a file. That's not just an optimization:
mixing a plain `<img src>` load and a `fetch()` call on the *same* URL
makes Chrome reuse a cache entry with no CORS metadata attached, which
then fails with a "no Access-Control-Allow-Origin header" error even
though the server sends one correctly — a real bug hit while building
this. See `api/routes_arena.py` for the server-side half of the fix.

## Project layout

```
frontend/
├── src/
│   ├── pages/
│   │   ├── ArenaPage.tsx, LiveMonitorPage.tsx, WebcamPage.tsx,
│   │   └── DriftPage.tsx, RegistryPage.tsx
│   ├── components/
│   │   ├── DetectionOverlay.tsx   # draws boxes on an image from a PredictionResult
│   │   ├── ImageUploader.tsx / MultiImageUploader.tsx
│   │   ├── FamilyBadge.tsx         # fixed color per model family (never cycled)
│   │   └── HealthBanner.tsx
│   ├── lib/api.ts                  # typed fetch wrapper for every endpoint
│   └── types.ts                    # mirrors the API's Pydantic schemas field-for-field
```

## Stack

Vite + React 19 + TypeScript + [Recharts](https://recharts.org/) (drift
chart only). Native `RTCPeerConnection` for WebRTC — no wrapper library.
No routing library — five tabs don't need one.

## Building for deployment

```bash
npm run build
```

Outputs a static site to `dist/`. Set `VITE_API_BASE_URL` at build time to
point at your deployed API:

```bash
VITE_API_BASE_URL=https://your-api.example.com npm run build
```
