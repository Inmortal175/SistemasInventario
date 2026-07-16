import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.domain.enums import UserRole
from app.infrastructure.database.connection import AsyncSessionLocal
from app.infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSockets"])

# Roles que reciben alertas del dashboard en tiempo real (HU-14).
_ALERT_ROLES = {UserRole.ADMIN, UserRole.SUPERADMIN}


class ConnectionManager:
    """Registro en memoria de conexiones WebSocket agrupadas por rol."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, group: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(group, set()).add(websocket)
        logger.info("WS_CONNECTED group=%s total=%s", group, len(self._connections[group]))

    async def disconnect(self, websocket: WebSocket, group: str) -> None:
        async with self._lock:
            conns = self._connections.get(group)
            if conns:
                conns.discard(websocket)

    async def broadcast(self, group: str, message: dict) -> None:
        """Retransmite un mensaje a todas las conexiones del grupo."""
        async with self._lock:
            targets = list(self._connections.get(group, set()))
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:  # noqa: BLE001 — conexión rota
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.get(group, set()).discard(ws)


# Grupo único de administradores (ADMIN + SUPERADMIN comparten el canal de alertas).
ADMIN_GROUP = "administrators"

manager = ConnectionManager()


@router.websocket("/notifications")
async def notifications_ws(
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    """HU-14-01: handshake WebSocket autenticado por JWT.

    Valida el token, asocia la conexión al grupo de Administradores y confirma
    la conexión con un mensaje de bienvenida.
    """
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4401)  # Unauthorized
        return

    async with AsyncSessionLocal() as session:
        user = await UserRepository(session).get_by_id(uuid.UUID(payload.sub))

    if user is None or not user.is_active or user.role not in _ALERT_ROLES:
        await websocket.close(code=4403)  # Forbidden
        return

    await manager.connect(websocket, ADMIN_GROUP)
    await websocket.send_json({
        "type": "connection_established",
        "message": "Conexión establecida. Suscrito a alertas en tiempo real.",
        "role": user.role.value,
    })
    try:
        while True:
            # Mantener viva la conexión; los mensajes entrantes se ignoran (canal de salida).
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket, ADMIN_GROUP)
        logger.info("WS_DISCONNECTED group=%s", ADMIN_GROUP)
