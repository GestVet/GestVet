"""Renderiza un texto como imagen QR.

Vive en el núcleo por la misma razón que `email.py` y `attachments.py`: no
conoce ningún tipo de negocio, solo recibe un texto y devuelve una imagen.
Lo usa el adaptador de pasarela de pago para mostrar el QR de cobro, pero no
sabe qué significa ese texto.
"""

from __future__ import annotations

import base64
from io import BytesIO

import qrcode


def render_qr_png_data_url(payload: str) -> str:
    image = qrcode.make(payload)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_qr_png(payload: str) -> bytes:
    """El QR como bytes PNG, para incrustarlo en un documento."""
    image = qrcode.make(payload)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
