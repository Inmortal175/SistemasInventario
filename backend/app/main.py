import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.middlewares.error_handlers import register_exception_handlers
from app.api.v1.router import api_router
from app.application.services.auth_service import AuthService
from app.core.config import get_settings
from app.infrastructure.cache.pubsub_listener import redis_alert_listener
from app.infrastructure.cache.redis_client import close_redis
from app.infrastructure.database.connection import AsyncSessionLocal
from app.infrastructure.repositories.settings_repository import SettingsRepository
from app.infrastructure.repositories.user_repository import UserRepository

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)
logger = logging.getLogger("app")


def apply_app_name(app: FastAPI, name: str) -> None:
    """Renombra la app y descarta el esquema OpenAPI ya generado.

    FastAPI cachea `openapi_schema` tras la primera petición a /openapi.json;
    sin invalidarlo, /docs seguiría mostrando el título anterior. Con varios
    workers, cada proceso se entera al arrancar o al atender el PATCH.
    """
    app.title = name
    app.openapi_schema = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Iniciando %s v%s (%s)", settings.app_name, settings.app_version, settings.environment)
    try:
        async with AsyncSessionLocal() as session:
            auth_service = AuthService(user_repo=UserRepository(session))
            await auth_service.create_initial_superadmin(
                email=settings.superadmin_email,
                password=settings.superadmin_password,
            )

            # La BD es la fuente de verdad del nombre; `settings.app_name` es
            # solo el valor de arranque para el primer boot. Sin esto, /docs
            # mostraría un nombre distinto al de la interfaz.
            db_settings = await SettingsRepository(session).get()
            apply_app_name(app, db_settings.app_name)

            await session.commit()
        logger.info("Seed de superadministrador verificado")
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo ejecutar el seed inicial: %s", exc)

    # HU-14: tarea en background que retransmite alertas Redis Pub/Sub → WebSocket.
    listener_task = asyncio.create_task(redis_alert_listener())

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass
    await close_redis()
    logger.info("Aplicación detenida limpiamente")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Sistema de Gestión de Inventario Inteligente y Dinámico para Pastelerías",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Alert-Triggered", "X-Cache-Status", "X-Cache"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    # Servir archivos estáticos (avatares, etc.)
    from pathlib import Path
    static_dir = Path("static")
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/health", tags=["Sistema"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name, "version": settings.app_version}

    return app


app = create_app()
