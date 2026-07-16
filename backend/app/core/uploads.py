"""Guardado de imágenes subidas (avatares, logo del sistema).

Sirve a `/static`, montado en `main.py`. El nombre del archivo nunca se toma
del cliente: se genera a partir de un prefijo del servidor más un sufijo
aleatorio, de modo que un `filename` malicioso no pueda escapar del directorio.
"""

import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024
# Un fondo a pantalla completa recortado por el navegador ronda 1–3 MB; 2 MB
# se queda corto y rechazaría fotos legítimas.
MAX_BACKGROUND_BYTES = 8 * 1024 * 1024

# Lado del logo normalizado. Se muestra como mucho a 96 px (menú) y 80 px
# (login); 512 deja margen para pantallas de alta densidad sin pesar de más.
SQUARE_LOGO_SIZE = 512


def _read_and_validate(
    file: UploadFile, content: bytes, max_bytes: int = MAX_IMAGE_BYTES
) -> None:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Formato no permitido. Usa JPG, PNG o WebP.",
        )
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La imagen supera el máximo de {max_bytes // (1024 * 1024)} MB.",
        )


def delete_static_file(url: str | None) -> None:
    """Borra un archivo servido bajo /static. Sin esto, cada reemplazo de logo o
    de fondo deja el anterior huérfano en disco para siempre.

    Silencioso a propósito: perder el archivo viejo no debe tumbar la petición
    que ya actualizó la base. Y la ruta se valida contra el directorio `static`
    para que un valor manipulado en la BD no pueda borrar fuera de él.
    """
    if not url or not url.startswith("/static/"):
        return
    root = Path("static").resolve()
    target = (root / url[len("/static/"):]).resolve()
    if root not in target.parents:
        return
    target.unlink(missing_ok=True)


def _write(content: bytes, subdir: str, filename: str) -> str:
    target_dir = Path("static") / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_bytes(content)
    return f"/static/{subdir}/{filename}"


async def save_fitted_image(
    file: UploadFile,
    subdir: str,
    stem: str,
    size: tuple[int, int],
    fmt: str = "PNG",
    max_bytes: int = MAX_IMAGE_BYTES,
) -> str:
    """Persiste la imagen ajustada exactamente a `size`, recortando al centro.

    El encuadre real lo elige el usuario en el navegador; aquí solo se garantiza
    la invariante. Decodificar con Pillow es lo único que prueba que el archivo
    es una imagen (el `content_type` lo declara el cliente), y el center-crop
    cubre a quien llame a la API sin pasar por la UI.
    """
    content = await file.read()
    _read_and_validate(file, content, max_bytes)

    try:
        with Image.open(BytesIO(content)) as img:
            # Las fotos de celular guardan la rotación en EXIF: sin esto, el
            # recorte se calcularía sobre una orientación distinta a la vista.
            oriented = ImageOps.exif_transpose(img)
            # JPEG no admite canal alfa; PNG lo conserva para logos calados.
            mode = "RGB" if fmt == "JPEG" else "RGBA"
            fitted = ImageOps.fit(
                oriented.convert(mode), size, method=Image.Resampling.LANCZOS
            )
            buffer = BytesIO()
            if fmt == "JPEG":
                fitted.save(buffer, format="JPEG", quality=82, optimize=True)
            else:
                fitted.save(buffer, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se pudo leer la imagen. ¿Está corrupta?",
        ) from exc

    ext = ".jpg" if fmt == "JPEG" else ".png"
    return _write(buffer.getvalue(), subdir, f"{stem}_{uuid.uuid4().hex[:8]}{ext}")


async def save_square_image(
    file: UploadFile, subdir: str, stem: str, size: int = SQUARE_LOGO_SIZE
) -> str:
    """Logo: 1:1 en PNG, para conservar la transparencia."""
    return await save_fitted_image(file, subdir, stem, (size, size), fmt="PNG")
