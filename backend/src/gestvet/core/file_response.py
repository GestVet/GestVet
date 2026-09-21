"""Respuesta HTTP que entrega un archivo guardado por la aplicación.

La comparten los adjuntos clínicos y la evidencia de reclamos. El nombre del
archivo lo escribió quien lo subió, así que no se confía en él para armar la
cabecera: se deja una versión ASCII segura y la original va codificada según
RFC 6266.
"""

from __future__ import annotations

import re
from urllib.parse import quote

from fastapi import Response

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _content_disposition(filename: str) -> str:
    fallback = _UNSAFE.sub("_", filename).strip("._") or "archivo"
    return f"inline; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename, safe='')}"


def inline_file_response(content: bytes, content_type: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": _content_disposition(filename),
            # El tipo sale de la lista cerrada que validó el dominio al subirlo;
            # sin esto el navegador podría adivinar otro y ejecutar el archivo.
            "X-Content-Type-Options": "nosniff",
            # Es dato clínico o de un reclamo: ningún caché compartido lo guarda.
            "Cache-Control": "private, no-store",
        },
    )
