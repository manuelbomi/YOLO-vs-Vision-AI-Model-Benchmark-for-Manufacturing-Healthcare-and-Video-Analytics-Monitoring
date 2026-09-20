from api import webhooks


def test_send_event_without_configured_url_records_error():
    webhooks.configure(None)
    result = webhooks.send_event("test", {"foo": "bar"})
    assert result["delivered"] is False
    assert "No webhook URL configured" in result["error"]


def test_send_event_to_unreachable_url_fails_gracefully(monkeypatch):
    webhooks.configure("http://127.0.0.1:1/unreachable")  # port 1: connection refused, fast
    result = webhooks.send_event("test", {"foo": "bar"})
    assert result["delivered"] is False
    assert result["error"] is not None
    # Doesn't raise -- a broken webhook endpoint must never break the caller.


def test_send_event_success_records_status_code(monkeypatch):
    import httpx

    def handler(request):
        assert request.url.path == "/hook"
        return httpx.Response(200, json={"ok": True})

    webhooks.configure("http://testserver/hook")
    monkeypatch.setattr(
        httpx, "post", lambda url, json, timeout: httpx.Client(transport=httpx.MockTransport(handler)).post(url, json=json)
    )

    result = webhooks.send_event("drift.significant", {"features": []})
    assert result["delivered"] is True
    assert result["status_code"] == 200

    webhooks.configure(None)  # reset global state for other tests
