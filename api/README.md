# API

FastAPI backend for the Vision Model Benchmark platform. See the main
[README](../README.md) for the full picture (architecture, cameras,
codecs, protocols, model families); this file is the endpoint reference.

## Running

```bash
uvicorn api.main:app --reload --port 8000
```

Run from the repo root, so `data/`, and the registry DB path all resolve.
Interactive docs: http://localhost:8000/docs

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Whether all 4 models finished loading |
| GET | `/api/arena/models` | List the 4 models with family/description/size |
| POST | `/api/arena/compare` | Run every model on an uploaded `file` or a bundled `sample_path` |
| GET | `/api/live/sources` | List available live sources (the bundled RTSP demo) |
| GET | `/api/live/stream?model=&source=` | Annotated MJPEG stream from a live source |
| POST | `/api/webrtc/offer` | WebRTC signaling: browser camera in, annotated video out |
| POST | `/api/drift/check` | PSI/KS/Cohen's d between a `reference` and `current` image batch |
| GET/POST | `/api/registry/models` | List / register model versions |
| POST | `/api/registry/models/{id}/promote` | Advance draft → staging → approved |
| POST | `/api/registry/models/{id}/archive` | Retire a model version |
| GET/POST | `/api/webhooks/config` | Get/set the outgoing webhook URL |
| POST | `/api/webhooks/test` | Fire a test event at the configured URL |

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated origins allowed to call this API |
| `DEMO_RTSP_URL` | `rtsp://127.0.0.1:8554/demo` | The RTSP source `source=demo` resolves to |
| `WEBHOOK_URL` | unset | Default outgoing webhook URL (can also be set at runtime via `/api/webhooks/config`) |
| `REGISTRY_DB_PATH` | `<repo root>/registry.db` | SQLite file location |

## A note on ports

Port 8000 is a common default that may already be in use by something
else on your machine (Docker Desktop, another dev server). If requests
from the frontend fail with a CORS or connection error but `curl
http://127.0.0.1:8000/api/health` works, something else is likely also
listening on that port — pick a different one and update
`frontend/.env.local`'s `VITE_API_BASE_URL` to match. `docker-compose.yml`
sidesteps this by using 8010 on the host by default.
