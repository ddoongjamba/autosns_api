"""
v1 라우터 집계
"""
from fastapi import APIRouter

from app.api.v1 import accounts, auth, captions, payments, posts, subscription, uploads

router = APIRouter()

router.include_router(auth.router)
router.include_router(accounts.router)
router.include_router(uploads.router)
router.include_router(posts.router)
router.include_router(captions.router)
router.include_router(subscription.router)
router.include_router(payments.router)
