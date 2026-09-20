from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from api import webhooks
from api.routes_webhooks import router
from api.webhooks_models import DeliveryStatus, WebhookDelivery


@pytest.fixture(autouse=True)
def isolated_engine(monkeypatch):
    """Every test gets its own in-memory SQLite engine, monkeypatched onto
    the webhooks module directly -- webhooks.py talks to the DB via a
    module-level `engine`, not FastAPI dependency injection, so isolating
    it this way (rather than a route-level dependency override) is what
    actually keeps tests from writing into the real registry.db file."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(webhooks, "engine", engine)
    yield engine
    webhooks.configure(None)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _mock_success_post(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(
        httpx, "post", lambda url, json, timeout: httpx.Client(transport=httpx.MockTransport(handler)).post(url, json=json)
    )


def test_send_event_without_configured_url_records_error():
    webhooks.configure(None)
    result = webhooks.send_event("test", {"foo": "bar"})
    assert result["delivered"] is False
    assert "No webhook URL configured" in result["error"]
    assert webhooks.list_deliveries() == []  # nothing to retry against, so nothing is persisted


def test_send_event_to_unreachable_url_persists_a_retrying_delivery():
    webhooks.configure("http://127.0.0.1:1/unreachable")  # port 1: connection refused, fast
    result = webhooks.send_event("test", {"foo": "bar"})
    assert result["delivered"] is False
    assert result["error"] is not None
    # Doesn't raise -- a broken webhook endpoint must never break the caller.

    deliveries = webhooks.list_deliveries()
    assert len(deliveries) == 1
    assert deliveries[0].status == DeliveryStatus.retrying
    assert deliveries[0].attempt_count == 1
    assert deliveries[0].next_attempt_at is not None


def test_send_event_success_persists_delivered(monkeypatch):
    webhooks.configure("http://testserver/hook")
    _mock_success_post(monkeypatch)

    result = webhooks.send_event("drift.significant", {"features": []})
    assert result["delivered"] is True
    assert result["status_code"] == 200

    deliveries = webhooks.list_deliveries()
    assert len(deliveries) == 1
    assert deliveries[0].status == DeliveryStatus.delivered
    assert deliveries[0].delivered_at is not None
    assert deliveries[0].next_attempt_at is None


def test_run_due_retries_skips_deliveries_not_yet_due():
    webhooks.configure("http://127.0.0.1:1/unreachable")
    webhooks.send_event("test", {})  # next_attempt_at lands ~30s in the future

    processed = webhooks.run_due_retries()
    assert processed == 0
    assert webhooks.list_deliveries()[0].attempt_count == 1


def test_run_due_retries_processes_deliveries_past_their_backoff_window(isolated_engine):
    webhooks.configure("http://127.0.0.1:1/unreachable")
    webhooks.send_event("test", {})
    delivery_id = webhooks.list_deliveries()[0].id

    with Session(isolated_engine) as session:
        row = session.get(WebhookDelivery, delivery_id)
        row.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.add(row)
        session.commit()

    processed = webhooks.run_due_retries()
    assert processed == 1
    assert webhooks.get_delivery(delivery_id).attempt_count == 2


def test_repeated_failures_mark_delivery_failed_after_max_attempts(isolated_engine):
    webhooks.configure("http://127.0.0.1:1/unreachable")
    webhooks.send_event("test", {})
    delivery_id = webhooks.list_deliveries()[0].id

    for _ in range(webhooks.MAX_ATTEMPTS - 1):
        with Session(isolated_engine) as session:
            row = session.get(WebhookDelivery, delivery_id)
            row.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            session.add(row)
            session.commit()
        webhooks.run_due_retries()

    final = webhooks.get_delivery(delivery_id)
    assert final.attempt_count == webhooks.MAX_ATTEMPTS
    assert final.status == DeliveryStatus.failed
    assert final.next_attempt_at is None


def test_manual_retry_bypasses_backoff_window_and_can_succeed(monkeypatch):
    webhooks.configure("http://127.0.0.1:1/unreachable")
    webhooks.send_event("test", {})
    delivery_id = webhooks.list_deliveries()[0].id

    # Simulate the receiving endpoint coming back up, then retry right
    # away rather than waiting out the ~30s backoff window.
    _mock_success_post(monkeypatch)
    updated = webhooks.retry_delivery_now(delivery_id)
    assert updated.status == DeliveryStatus.delivered
    assert updated.attempt_count == 2


def test_api_lists_and_retries_deliveries(client, monkeypatch):
    webhooks.configure("http://127.0.0.1:1/unreachable")
    client.post("/api/webhooks/test")

    listing = client.get("/api/webhooks/deliveries").json()
    assert len(listing) == 1
    assert listing[0]["status"] == "retrying"
    delivery_id = listing[0]["id"]

    _mock_success_post(monkeypatch)
    retried = client.post(f"/api/webhooks/deliveries/{delivery_id}/retry").json()
    assert retried["status"] == "delivered"

    assert client.get("/api/webhooks/deliveries/999999").status_code == 404
    assert client.post("/api/webhooks/deliveries/999999/retry").status_code == 404
