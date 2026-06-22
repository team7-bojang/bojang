"""환경변수 기반 설정 (pydantic-settings).

`.env` 파일 또는 OS 환경변수에서 값을 읽는다. `.env.example` 참고.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 서버 ──
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = True

    # ── CORS (프론트엔드 주소) ──
    cors_origins: list[str] = ["http://localhost:5173"]

    # ── Supabase / DB ──
    supabase_url: str = ""
    supabase_key: str = ""
    database_url: str = ""
    # Supabase JWT 검증(HS256 대칭키). 대시보드 Settings → API → JWT Secret.
    supabase_jwt_secret: str = ""
    supabase_jwt_audience: str = "authenticated"

    # ── LLM ──
    openai_api_key: str = ""
    anthropic_api_key: str = ""


settings = Settings()
