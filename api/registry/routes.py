from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .db import get_session
from .schemas import ApprovalStatus, ModelVersion, ModelVersionCreate, ModelVersionRead

router = APIRouter(prefix="/api/registry", tags=["registry"])


@router.get("/models", response_model=list[ModelVersionRead])
def list_models(session: Session = Depends(get_session)):
    return session.exec(select(ModelVersion)).all()


@router.post("/models", response_model=ModelVersionRead)
def create_model(payload: ModelVersionCreate, session: Session = Depends(get_session)):
    model = ModelVersion.model_validate(payload)
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


@router.get("/models/{model_id}", response_model=ModelVersionRead)
def get_model(model_id: int, session: Session = Depends(get_session)):
    model = session.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(404, "Model version not found")
    return model


def _transition(model_id: int, session: Session, new_status: ApprovalStatus, stamp_promoted: bool):
    model = session.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(404, "Model version not found")
    model.approval_status = new_status
    if stamp_promoted:
        model.promoted_at = datetime.now(timezone.utc)
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


@router.post("/models/{model_id}/promote", response_model=ModelVersionRead)
def promote_model(model_id: int, session: Session = Depends(get_session)):
    """Advances draft -> staging -> approved. Calling it on an already-approved
    model is a no-op (idempotent), not an error."""
    model = session.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(404, "Model version not found")
    next_status = {
        ApprovalStatus.draft: ApprovalStatus.staging,
        ApprovalStatus.staging: ApprovalStatus.approved,
        ApprovalStatus.approved: ApprovalStatus.approved,
    }.get(model.approval_status, ApprovalStatus.staging)
    return _transition(model_id, session, next_status, stamp_promoted=True)


@router.post("/models/{model_id}/archive", response_model=ModelVersionRead)
def archive_model(model_id: int, session: Session = Depends(get_session)):
    return _transition(model_id, session, ApprovalStatus.archived, stamp_promoted=False)
