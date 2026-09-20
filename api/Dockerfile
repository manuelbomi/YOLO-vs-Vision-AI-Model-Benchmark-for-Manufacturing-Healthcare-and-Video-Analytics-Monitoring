FROM python:3.10-slim

WORKDIR /app

# System deps: libgl1/libglib2.0 for opencv-python, ffmpeg headers already
# covered by the aiortc wheel on this base image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Pre-download every model's weights at build time, not first request --
# so the container starts serving immediately instead of a multi-minute
# first request while YOLO/DETR/BLIP download in the background.
COPY api ./api
RUN python -c "from api.models.loader import MODEL_CLASSES; [cls() for cls in MODEL_CLASSES]"

COPY data ./data
COPY scripts ./scripts

EXPOSE 8000
ENV REGISTRY_DB_PATH=/app/registry.db

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
