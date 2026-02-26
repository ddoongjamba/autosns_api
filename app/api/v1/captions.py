"""
AI 캡션 생성 API: /captions/generate
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_current_user
from app.models.user import User
from app.schemas.caption import GenerateCaptionRequest, GenerateCaptionResponse
from app.services import caption_service

router = APIRouter(prefix="/captions", tags=["captions"])


@router.post("/generate", response_model=GenerateCaptionResponse)
async def generate_caption(
    req: GenerateCaptionRequest,
    current_user: User = Depends(get_current_user),
):
    """AI를 사용해 Instagram 캡션과 해시태그를 생성한다."""
    try:
        return await caption_service.generate_caption(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
