from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api import webhooks
from api.webhooks_models import WebhookDeliveryRead

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


@router.get("/deliveries", response_model=list[WebhookDeliveryRead])
def list_deliveries(limit: int = 50):
    """Delivery history, most recent first -- includes attempt count, last
    error, and (for a still-retrying delivery) when it'll next be tried."""
    return webhooks.list_deliveries(limit=limit)


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryRead)
def get_delivery(delivery_id: int):
    delivery = webhooks.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(404, "Delivery not found")
    return delivery


@router.post("/deliveries/{delivery_id}/retry", response_model=WebhookDeliveryRead)
def retry_delivery(delivery_id: int):
    """Retries immediately, bypassing the backoff window -- for after
    you've fixed whatever was wrong with the receiving endpoint."""
    delivery = webhooks.retry_delivery_now(delivery_id)
    if not delivery:
        raise HTTPException(404, "Delivery not found")
    return delivery
