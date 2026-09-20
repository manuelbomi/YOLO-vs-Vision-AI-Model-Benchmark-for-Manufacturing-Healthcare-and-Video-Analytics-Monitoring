from fastapi import APIRouter
from pydantic import BaseModel

from api import webhooks

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class WebhookConfig(BaseModel):
    url: str | None = None


@router.get("/config")
def get_config():
    return {"url": webhooks.get_configured_url(), "last_delivery": webhooks.get_last_delivery()}


@router.post("/config")
def set_config(config: WebhookConfig):
    webhooks.configure(config.url)
    return {"url": webhooks.get_configured_url()}


@router.post("/test")
def send_test_event():
    return webhooks.send_event(
        "test",
        {"message": "This is a test event from the Vision Model Benchmark platform."},
    )
