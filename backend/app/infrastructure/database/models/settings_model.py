import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import ThemeName
from app.infrastructure.database.base import Base, TimestampMixin

SETTINGS_ID = 1


class SystemSettingsModel(Base, TimestampMixin):
    """Identidad visual de la instalación: nombre, logo y paleta.

    Fila única: el CHECK sobre la PK hace imposible insertar una segunda
    configuración, así que ninguna lectura necesita desempatar entre filas.
    """
    __tablename__ = "system_settings"

    __table_args__ = (
        CheckConstraint(f"id = {SETTINGS_ID}", name="chk_settings_singleton"),
        CheckConstraint(
            "login_overlay_opacity BETWEEN 0 AND 80", name="chk_settings_overlay"
        ),
        CheckConstraint(
            "expiration_alert_days BETWEEN 1 AND 90", name="chk_settings_expiration_days"
        ),
        CheckConstraint("page_size BETWEEN 5 AND 100", name="chk_settings_page_size"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=SETTINGS_ID)

    app_name: Mapped[str] = mapped_column(
        String(80), nullable=False, default="PastryStock Manager"
    )
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    theme: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ThemeName.ROSA.value
    )

    # Fondos del login, uno por familia de dispositivo. Cualquiera puede faltar:
    # el frontend cae al del tamaño inmediatamente mayor.
    login_bg_mobile_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    login_bg_tablet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    login_bg_desktop_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Opacidad del velo sobre el fondo del login, en porcentaje.
    login_overlay_opacity: Mapped[int] = mapped_column(Integer, nullable=False, default=40)

    # ── Reglas de negocio de la pastelería ───────────────────────────────────
    # Cuántos días antes del vencimiento avisar. Vivía en una variable de
    # entorno, pero es una decisión del negocio, no del despliegue.
    expiration_alert_days: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="es-PE")
    page_size: Mapped[int] = mapped_column(Integer, nullable=False, default=15)

    # ── Identidad fiscal, para membretes de reportes ─────────────────────────
    business_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<SystemSettingsModel app_name={self.app_name} theme={self.theme}>"
