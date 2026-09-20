"""Outgoing webhooks: the "push" side of integrating this platform into a
larger system (an alerting channel, a ticketing system, a SCADA/MES bridge
-- see README > Networking protocols). A webhook here is just an HTTP POST
of a JSON event to a URL you configure; there's no special protocol beyond
plain HTTP, which is exactly why it's the lowest-friction integration point
of the three this repo demonstrates (RTSP in, WebRTC in, webhook out).

Deliberately in-memory, not persisted -- this is a demo/reference
implementation. A production deployment would want a durable queue with
retries; see README > Known limitations.
"""
import logging
import os
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("webhooks")

_configured_url: str | None = os.environ.get("WEBHOOK_URL")
_last_delivery: dict | None = None


def configure(url: str | None):
    global _configured_url
    _configured_url = url or None


def get_configured_url() -> str | None:
    return _configured_url


def get_last_delivery() -> dict | None:
    return _last_delivery


def send_event(event_type: str, payload: dict) -> dict:
    """Fire-and-log: a webhook delivery failure never raises into the
    caller's request path (a drift check or live-monitor frame shouldn't
    fail just because someone's alerting endpoint is down)."""
    global _last_delivery
    body = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    result = {"url": _configured_url, "event": event_type, "delivered": False, "error": None}

    if not _configured_url:
        result["error"] = "No webhook URL configured"
        _last_delivery = result
        return result

    try:
        response = httpx.post(_configured_url, json=body, timeout=5.0)
        result["delivered"] = response.status_code < 400
        result["status_code"] = response.status_code
    except httpx.HTTPError as e:
        result["error"] = str(e)
        logger.warning("Webhook delivery to %s failed: %s", _configured_url, e)

    _last_delivery = result
    return result
