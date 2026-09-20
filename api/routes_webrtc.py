from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.ingestion.webrtc import handle_offer
from api.models.loader import loader

router = APIRouter(prefix="/api/webrtc", tags=["webrtc"])


class WebRTCOffer(BaseModel):
    sdp: str
    type: str
    model: str


class WebRTCAnswer(BaseModel):
    sdp: str
    type: str


@router.post("/offer", response_model=WebRTCAnswer)
async def offer(body: WebRTCOffer):
    if loader.get(body.model) is None:
        raise HTTPException(404, f"Unknown model '{body.model}'")
    answer = await handle_offer(body.sdp, body.type, body.model)
    return WebRTCAnswer(sdp=answer.sdp, type=answer.type)
