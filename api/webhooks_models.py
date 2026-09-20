"""Persistence for outgoing webhook deliveries, including retry state.

Uses the same SQLite file as the model registry (see api/registry/db.py) --
this is a single-writer demo/reference app with one persistence layer, not
a separate database per feature.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


class DeliveryStatus(str, Enum):
    delivered = "delivered"
    retrying = "retrying"
    failed = "failed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WebhookDelivery(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str
    url: str
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    status: DeliveryStatus = Field(default=DeliveryStatus.retrying)
    attempt_count: int = 0
    last_status_code: Optional[int] = None
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    last_attempt_at: Optional[datetime] = None
    next_attempt_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class WebhookDeliveryRead(SQLModel):
    id: int
    event_type: str
    url: str
    payload: dict
    status: DeliveryStatus
    attempt_count: int
    last_status_code: Optional[int]
    last_error: Optional[str]
    created_at: datetime
    last_attempt_at: Optional[datetime]
    next_attempt_at: Optional[datetime]
    delivered_at: Optional[datetime]
