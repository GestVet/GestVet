"""Adaptador de almacenamiento de archivos.

Vive en el núcleo por la misma razón que `email.py`: no conoce ningún tipo de
negocio, solo recibe una clave y bytes. Satisface el puerto `AttachmentStorage`
de `medical_records` y `EvidenceStorage` de `complaints` por estructura.

Ninguno de los dos adaptadores publica el archivo: se lee de vuelta con `read`
y lo entrega la API después de comprobar quién lo pide. Una radiografía o la
evidencia de un reclamo no pueden quedar al alcance de cualquiera que tenga el
enlace.

- `LocalDiskAttachmentStorage`: guarda el archivo en el disco local. Sirve en
  desarrollo y en pruebas locales.
- `SupabaseAttachmentStorage`: guarda el archivo en un bucket privado de
  Supabase Storage por su API REST con `httpx`, autenticado con la clave de
  rol de servicio. Sirve en Render Free y en cualquier entorno sin disco
  persistente.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import httpx

if TYPE_CHECKING:
    from gestvet.core.config import Settings


class AttachmentStorageProtocol(Protocol):
    async def save(self, key: str, content: bytes, content_type: str) -> None: ...
    async def read(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> None: ...


class LocalDiskAttachmentStorage:
    def __init__(self, storage_dir: str) -> None:
        self._storage_dir = Path(storage_dir)

    async def save(self, key: str, content: bytes, content_type: str) -> None:
        del content_type  # el disco no distingue tipos; lo guarda la referencia en la base
        await asyncio.to_thread(self._write, key, content)

    async def read(self, key: str) -> bytes:
        return await asyncio.to_thread(self._path(key).read_bytes)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._path(key).unlink, True)

    def _write(self, key: str, content: bytes) -> None:
        destination = self._path(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def _path(self, key: str) -> Path:
        # La clave la arma el servidor, pero si alguna vez llegara con `..` no
        # debe poder salir del directorio de adjuntos.
        root = self._storage_dir.resolve()
        destination = (root / key.lstrip("/")).resolve()
        if not destination.is_relative_to(root):
            raise FileNotFoundError(key)
        return destination


class SupabaseAttachmentStorage:
    """Almacenamiento de archivos en Supabase Storage vía API REST.

    Usa `httpx` directamente para interactuar con el bucket sin agregar el SDK
    pesado de Supabase. La clave de rol de servicio (`service_role_key`) da
    permiso para subir, leer y borrar en un bucket privado, así que el bucket
    no necesita ninguna política pública.
    """

    def __init__(
        self,
        supabase_url: str,
        service_role_key: str,
        bucket: str = "attachments",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key
        self._bucket = bucket
        self._client = client

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self._service_role_key,
            "Authorization": f"Bearer {self._service_role_key}",
        }
        if content_type:
            headers["Content-Type"] = content_type
            headers["x-upsert"] = "true"
        return headers

    def _object_url(self, key: str) -> str:
        return f"{self._supabase_url}/storage/v1/object/{self._bucket}/{key.lstrip('/')}"

    async def _send(
        self, method: str, key: str, *, content_type: str | None = None, content: bytes = b""
    ) -> httpx.Response:
        url = self._object_url(key)
        headers = self._headers(content_type)
        body = content or None
        if self._client is not None:
            return await self._client.request(method, url, content=body, headers=headers)
        async with httpx.AsyncClient() as client:
            return await client.request(method, url, content=body, headers=headers)

    async def save(self, key: str, content: bytes, content_type: str) -> None:
        response = await self._send("POST", key, content_type=content_type, content=content)
        response.raise_for_status()

    async def read(self, key: str) -> bytes:
        response = await self._send("GET", key)
        # Supabase responde 400 con "Object not found" además de 404, según la versión.
        if response.status_code in (400, 404):
            raise FileNotFoundError(key)
        response.raise_for_status()
        return response.content

    async def delete(self, key: str) -> None:
        response = await self._send("DELETE", key)
        if response.status_code not in (200, 204, 404):
            response.raise_for_status()


def create_attachment_storage(settings: Settings | None = None) -> AttachmentStorageProtocol:
    """Fábrica compartida para instanciar el adaptador de almacenamiento configurado."""
    from gestvet.core.config import get_settings

    cfg = settings or get_settings()
    if cfg.supabase_url.strip() and cfg.supabase_service_role_key.strip():
        return SupabaseAttachmentStorage(
            supabase_url=cfg.supabase_url,
            service_role_key=cfg.supabase_service_role_key,
            bucket=cfg.supabase_storage_bucket,
        )
    return LocalDiskAttachmentStorage(storage_dir=cfg.attachments_storage_dir)
