from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Aplicación ───────────────────────────────────────────────────────────
    app_name: str = "PastryStock Manager"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Base de datos ────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://pastry_user:pastry_secret@localhost:5432/pastry_inventory",
        description="URL async para SQLAlchemy (asyncpg)",
    )
    database_url_sync: str = Field(
        default="postgresql://pastry_user:pastry_secret@localhost:5432/pastry_inventory",
        description="URL sync para Alembic migrations",
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = Field(
        default="redis://:redis_secret@localhost:6379/0",
        description="URL de conexión Redis con contraseña",
    )
    redis_cache_ttl: int = Field(default=3600, description="TTL en segundos para caché de categorías")

    # ── JWT / Seguridad ──────────────────────────────────────────────────────
    secret_key: str = Field(
        default="changeme-use-openssl-rand-hex-32-in-prod",
        min_length=32,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    # ── Seed Superadmin ──────────────────────────────────────────────────────
    superadmin_email: str = "admin@pastry.local"
    superadmin_password: str = Field(default="Admin@12345", min_length=8)

    # ── Alertas de stock ─────────────────────────────────────────────────────
    redis_alert_channel: str = "alerts:low_stock"
    redis_expiration_channel: str = "alerts:expiration_critical"

    # ── Rate limiting de login (HU-04-02) ────────────────────────────────────
    login_max_attempts: int = 5
    login_window_seconds: int = 900        # 15 minutos
    login_block_seconds: int = 900         # bloqueo de la IP

    # El umbral de días para la alerta de vencimiento (HU-13-03) vive ahora en
    # `system_settings.expiration_alert_days`: lo decide la pastelería, no el
    # despliegue, y cambiarlo no debe exigir reiniciar el contenedor.

    # ── Helpers ──────────────────────────────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton de configuración. Se cachea en memoria tras la primera lectura."""
    return Settings()
