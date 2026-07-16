import uuid
from pydantic import BaseModel, EmailStr
from app.domain.enums import UserRole


class LoginRequest(BaseModel):
    username: str   # OAuth2PasswordRequestForm usa "username" (mapeamos al email)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int             # minutos
    user_id: uuid.UUID
    full_name: str
    role: UserRole
    avatar_url: str | None = None
