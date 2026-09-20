"""The model registry's data model: a minimal, self-contained governance
record per model version. This is deliberately not MLflow -- no tracking
server, no artifact store, just enough structure (version, metrics,
approval workflow) to demonstrate what model governance means in practice.
See README > Model governance for the scoping rationale and the
draft -> staging -> approved -> archived workflow this enum encodes.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


class ApprovalStatus(str, Enum):
    draft = "draft"
    staging = "staging"
    approved = "approved"
    archived = "archived"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModelVersionBase(SQLModel):
    name: str
    version: str = "1.0.0"
    family: str
    framework: str
    task_type: str
    approx_download_mb: int = 0
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSON))
    notes: str = ""


class ModelVersion(ModelVersionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.draft)
    created_at: datetime = Field(default_factory=_utcnow)
    promoted_at: Optional[datetime] = None


class ModelVersionCreate(ModelVersionBase):
    pass


class ModelVersionRead(ModelVersionBase):
    id: int
    approval_status: ApprovalStatus
    created_at: datetime
    promoted_at: Optional[datetime]
