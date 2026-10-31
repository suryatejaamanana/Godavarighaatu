from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "product-images"

    # --- image storage ---
    storage_backend: Literal["local", "supabase"] = (
        "local"  # local: dev only, files under media_root
    )
    media_root: str = "media"
    public_media_url: str = "http://localhost:8000/media"  # how browsers reach local files
    max_upload_mb: int = 10

    # --- admin authentication ---
    jwt_secret: str = ""
    access_token_minutes: int = 15
    refresh_token_days: int = 7  # sliding: renewed on every refresh
    session_max_days: int = 30  # absolute limit, regardless of refreshes
    cookie_secure: bool = False  # must be True in production (HTTPS)
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None
    rate_limit_enabled: bool = True
    login_rate_limit: str = "5/minute"
    refresh_rate_limit: str = "30/minute"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    def validate_for_runtime(self) -> None:
        """Refuse to start with an insecure configuration outside development."""
        if self.is_development:
            return
        problems = []
        if len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET must be at least 32 characters")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            problems.append("SameSite=None requires COOKIE_SECURE=true")
        if self.storage_backend == "local":
            problems.append("STORAGE_BACKEND must be 'supabase' (local disk is for development)")
        if "*" in self.cors_origins:
            problems.append("CORS_ORIGINS must not contain '*'")
        if problems:
            raise RuntimeError("Insecure configuration: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
