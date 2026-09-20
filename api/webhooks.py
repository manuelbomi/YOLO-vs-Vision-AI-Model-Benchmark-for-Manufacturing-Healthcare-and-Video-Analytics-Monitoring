"""Outgoing webhooks: the "push" side of integrating this platform into a
larger system (an alerting channel, a ticketing system, a SCADA/MES bridge
-- see README > Networking protocols). A webhook here is just an HTTP POST
of a JSON event to a URL you configure; there's no special protocol beyond
plain HTTP, which is exactly why it's the lowest-friction integration point
of the three this repo demonstrates (RTSP in, WebRTC in, webhook out).

Deliveries are persisted (see api/webhooks_models.WebhookDelivery), and a
failed delivery is retried with exponential backoff by the background
worker in api/webhooks_worker.py -- this is what makes it durable rather
than "logged and forgotten": a webhook endpoint that's down for a few
minutes during a deploy doesn't silently lose events.
"""
import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
from sqlmodel import Session, select

from api.registry.db import engine
from api.webhooks_models import DeliveryStatus, WebhookDelivery

logger = logging.getLogger("webhooks")

_configured_url: str | None = os.environ.get("WEBHOOK_URL")

# 5 attempts total, doubling each time: ~30s, 60s, 120s, 240s after the
# first (immediate) attempt -- long enough to ride out a short restart of
# whatever's on the other end, without retrying forever.
MAX_ATTEMPTS = 5
BASE_BACKOFF_SECONDS = 30


def configure(url: str | None):
    global _configured_url
    _configured_url = url or None


def get_configured_url() -> str | None:
    return _configured_url


def _backoff_seconds(attempt_count: int) -> float:
    return BASE_BACKOFF_SECONDS * (2 ** (attempt_count - 1))


def _as_result(delivery: WebhookDelivery) -> dict:
    return {
        "url": delivery.url,
        "event": delivery.event_type,
        "delivered": delivery.status == DeliveryStatus.delivered,
        "error": delivery.last_error,
        "status_code": delivery.last_status_code,
        "delivery_id": delivery.id,
    }


def _schedule_retry_or_fail(delivery: WebhookDelivery) -> None:
    if delivery.attempt_count >= MAX_ATTEMPTS:
        delivery.status = DeliveryStatus.failed
        delivery.next_attempt_at = None
    else:
        delivery.status = DeliveryStatus.retrying
        delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(
            seconds=_backoff_seconds(delivery.attempt_count)
        )


def _attempt_delivery(session: Session, delivery: WebhookDelivery) -> dict:
    """Makes one HTTP POST attempt and updates the delivery row in place.
    Never raises -- a broken webhook endpoint must never break the
    caller's request path (a drift check or live-monitor frame shouldn't
    fail just because someone's alerting endpoint is down)."""
    delivery.attempt_count += 1
    delivery.last_attempt_at = datetime.now(timezone.utc)
    body = {
        "event": delivery.event_type,
        "timestamp": delivery.created_at.isoformat(),
        "payload": delivery.payload,
    }

    try:
        response = httpx.post(delivery.url, json=body, timeout=5.0)
        delivery.last_status_code = response.status_code
        if response.status_code < 400:
            delivery.status = DeliveryStatus.delivered
            delivery.delivered_at = datetime.now(timezone.utc)
            delivery.next_attempt_at = None
            delivery.last_error = None
        else:
            delivery.last_error = f"HTTP {response.status_code}"
            _schedule_retry_or_fail(delivery)
    except httpx.HTTPError as e:
        delivery.last_error = str(e)
        logger.warning("Webhook delivery to %s failed: %s", delivery.url, e)
        _schedule_retry_or_fail(delivery)

    session.add(delivery)
    session.commit()
    session.refresh(delivery)
    return _as_result(delivery)


def send_event(event_type: str, payload: dict) -> dict:
    """Records the event and makes an immediate first delivery attempt. If
    that attempt fails, the row is left in "retrying" state with a
    next_attempt_at for the background worker to pick up -- see
    api/webhooks_worker.py for why retries happen there instead of in a
    blocking loop right here."""
    if not _configured_url:
        return {"url": None, "event": event_type, "delivered": False, "error": "No webhook URL configured"}

    with Session(engine) as session:
        delivery = WebhookDelivery(event_type=event_type, url=_configured_url, payload=payload)
        session.add(delivery)
        session.commit()
        session.refresh(delivery)
        return _attempt_delivery(session, delivery)


def get_last_delivery() -> dict | None:
    with Session(engine) as session:
        row = session.exec(select(WebhookDelivery).order_by(WebhookDelivery.id.desc())).first()
        return _as_result(row) if row else None


def list_deliveries(limit: int = 50) -> list[WebhookDelivery]:
    with Session(engine) as session:
        return session.exec(
            select(WebhookDelivery).order_by(WebhookDelivery.id.desc()).limit(limit)
        ).all()


def get_delivery(delivery_id: int) -> WebhookDelivery | None:
    with Session(engine) as session:
        return session.get(WebhookDelivery, delivery_id)


def retry_delivery_now(delivery_id: int) -> WebhookDelivery | None:
    """Manual retry, bypassing next_attempt_at -- for when you've fixed
    the endpoint and don't want to wait out the backoff window."""
    with Session(engine) as session:
        delivery = session.get(WebhookDelivery, delivery_id)
        if not delivery:
            return None
        _attempt_delivery(session, delivery)
        return delivery


def run_due_retries() -> int:
    """Attempts every delivery whose backoff window has elapsed. Called
    periodically by api/webhooks_worker.py. Returns the number processed."""
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        due = session.exec(
            select(WebhookDelivery).where(
                WebhookDelivery.status == DeliveryStatus.retrying,
                WebhookDelivery.next_attempt_at <= now,
            )
        ).all()
        for delivery in due:
            _attempt_delivery(session, delivery)
        return len(due)
