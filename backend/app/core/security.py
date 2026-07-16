import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt import PyJWTError
from pydantic import BaseModel

from app.core.config import get_settings

_settings = get_settings()

# bcrypt opera sobre un máximo de 72 bytes; bcrypt>=5 lanza si se excede.
# Truncamos explícitamente para aceptar contraseñas largas sin romper el hash.
_BCRYPT_MAX_BYTES = 72


class TokenPayload(BaseModel):
    sub: str    # user_id como string
    role: str
    exp: datetime
    iat: datetime | None = None   # issued-at: permite invalidar tokens previos a un reset


def _encode(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_encode(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_encode(plain), hashed.encode("utf-8"))
    except ValueError:
        # Hash malformado en BD → tratar como no coincidente en lugar de romper.
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=_settings.access_token_expire_minutes)
    payload: dict[str, object] = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, _settings.secret_key, algorithm=_settings.algorithm)


def decode_access_token(token: str) -> TokenPayload | None:
    try:
        raw = jwt.decode(token, _settings.secret_key, algorithms=[_settings.algorithm])
        return TokenPayload(**raw)
    except PyJWTError:
        return None
