from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ThemeName

# Códigos ISO: 4217 para la moneda, BCP-47 para el locale. Se validan por patrón
# y no contra una lista cerrada: mantener el catálogo entero sería peor negocio
# que aceptar un código raro que solo afecta al formato de los números.
_CURRENCY_PATTERN = r"^[A-Z]{3}$"
_LOCALE_PATTERN = r"^[a-z]{2}(-[A-Z]{2})?$"


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    app_name: str
    logo_url: str | None
    theme: ThemeName

    login_bg_mobile_url: str | None
    login_bg_tablet_url: str | None
    login_bg_desktop_url: str | None
    login_overlay_opacity: int

    expiration_alert_days: int
    currency_code: str
    locale: str
    page_size: int

    business_name: str | None
    tax_id: str | None
    address: str | None
    phone: str | None

    updated_at: datetime


class SettingsUpdate(BaseModel):
    """Las imágenes no se tocan aquí: cada una tiene su endpoint de subida.

    Todo es opcional: un None significa «no cambiar este campo». Los campos de
    texto libre admiten cadena vacía como forma de borrarlos.
    """

    app_name: str | None = Field(default=None, min_length=2, max_length=80)
    theme: ThemeName | None = None

    login_overlay_opacity: int | None = Field(default=None, ge=0, le=80)

    expiration_alert_days: int | None = Field(default=None, ge=1, le=90)
    currency_code: str | None = Field(
        default=None, pattern=_CURRENCY_PATTERN, examples=["PEN"]
    )
    locale: str | None = Field(default=None, pattern=_LOCALE_PATTERN, examples=["es-PE"])
    page_size: int | None = Field(default=None, ge=5, le=100)

    business_name: str | None = Field(default=None, max_length=150)
    tax_id: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
