"""
환경 변수 설정 (Pydantic BaseSettings)
"""
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # JWT
    SECRET_KEY: str = "dev-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Fernet (IG 비밀번호 암호화)
    FERNET_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./autosns.db"

    # AI
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    AI_PROVIDER: str = "openai"  # "openai" | "anthropic"

    # 아임포트 (PortOne)
    IMP_KEY: str = ""      # REST API 키
    IMP_SECRET: str = ""   # REST API Secret

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # 파일 저장 경로 (프로젝트 루트 기준)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    SESSIONS_DIR: Path = BASE_DIR / "sessions"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


settings = Settings()

# 필요 디렉토리 자동 생성
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
