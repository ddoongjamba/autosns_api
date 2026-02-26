"""
보안: JWT, bcrypt, Fernet 암호화
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── 비밀번호 ────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── JWT ─────────────────────────────────────────────────────────────────────

def _create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id), "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> Optional[dict]:
    """토큰 디코딩. 유효하지 않으면 None 반환."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# ─── Fernet (IG 비밀번호 암호화) ─────────────────────────────────────────────

def _get_fernet() -> Fernet:
    key = settings.FERNET_KEY
    if not key:
        # 키가 없으면 자동 생성 (개발용 — 프로덕션에서는 .env에 명시)
        key = Fernet.generate_key().decode()
        settings.FERNET_KEY = key
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_password(plain: str) -> str:
    """평문 IG 비밀번호 → Fernet 암호화 문자열."""
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """Fernet 암호화 문자열 → 평문."""
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken as e:
        raise ValueError("IG 비밀번호 복호화 실패") from e
