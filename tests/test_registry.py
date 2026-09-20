import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from api.registry.db import get_session
from api.registry.routes import router
from fastapi import FastAPI


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def _override_session():
        with Session(engine) as session:
            yield session

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_session] = _override_session
    return TestClient(app)


def _create_payload(name="TestModel"):
    return {
        "name": name,
        "version": "1.0.0",
        "family": "yolo",
        "framework": "ultralytics",
        "task_type": "object-detection",
        "approx_download_mb": 6,
        "metrics": {"latency_ms": 100},
    }


def test_create_and_list_model(client):
    response = client.post("/api/registry/models", json=_create_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "TestModel"
    assert body["approval_status"] == "draft"

    listing = client.get("/api/registry/models").json()
    assert len(listing) == 1


def test_promote_workflow_advances_one_step_at_a_time(client):
    created = client.post("/api/registry/models", json=_create_payload()).json()
    model_id = created["id"]

    step1 = client.post(f"/api/registry/models/{model_id}/promote").json()
    assert step1["approval_status"] == "staging"

    step2 = client.post(f"/api/registry/models/{model_id}/promote").json()
    assert step2["approval_status"] == "approved"

    # idempotent once approved
    step3 = client.post(f"/api/registry/models/{model_id}/promote").json()
    assert step3["approval_status"] == "approved"


def test_archive_model(client):
    created = client.post("/api/registry/models", json=_create_payload()).json()
    model_id = created["id"]

    archived = client.post(f"/api/registry/models/{model_id}/archive").json()
    assert archived["approval_status"] == "archived"


def test_get_missing_model_returns_404(client):
    response = client.get("/api/registry/models/999")
    assert response.status_code == 404
