"""Adaptador de almacenamiento de archivos.

Vive en el núcleo por la misma razón que `email.py`: no conoce ningún tipo de
negocio, solo recibe una clave y bytes. Satisface el puerto `AttachmentStorage`
de `medical_records` y `EvidenceStorage` de `complaints` por estructura.

Ofrece dos adaptadores:
- `LocalDiskAttachmentStorage`: guarda el archivo en disco local y lo sirve
  como archivo estático. Útil en desarrollo y pruebas locales.
- `SupabaseAttachmentStorage`: sube los archivos directamente a un bucket
  público de Supabase Storage mediante su API REST usando `httpx`, devolviendo
  la URL pública del archivo. Ideal para Render Free u entornos sin disco persistente.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import httpx

if TYPE_CHECKING:
    from gestvet.core.config import Settings


class AttachmentStorageProtocol(Protocol):
    async def save(self, key: str, content: bytes, content_type: str) -> str: ...
    async def delete(self, key: str) -> None: ...


class LocalDiskAttachmentStorage:
    def __init__(self, storage_dir: str, public_base_url: str) -> None:
        self._storage_dir = Path(storage_dir)
        self._public_base_url = public_base_url.rstrip("/")

    async def save(self, key: str, content: bytes, content_type: str) -> str:
        del content_type  # el disco no distingue tipos; lo hace el navegador al leerlo
        await asyncio.to_thread(self._write, key, content)
        return f"{self._public_base_url}/{key.lstrip('/')}"

    async def delete(self, key: str) -> None:
        await asyncio.to_thread((self._storage_dir / key).unlink, True)

    def _write(self, key: str, content: bytes) -> None:
        destination = self._storage_dir / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


class SupabaseAttachmentStorage:
    """Almacenamiento de archivos en Supabase Storage vía API REST.

    Usa `httpx` directamente para interactuar con el bucket sin agregar el SDK
    pesado de Supabase. Requiere la clave de rol de servicio (`service_role_key`)
    para tener permisos de escritura y borrado directos.
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

    async def save(self, key: str, content: bytes, content_type: str) -> str:
        clean_key = key.lstrip("/")
        url = f"{self._supabase_url}/storage/v1/object/{self._bucket}/{clean_key}"
        headers = self._headers(content_type)
        if self._client is not None:
            response = await self._client.post(url, content=content, headers=headers)
            response.raise_for_status()
        else:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, content=content, headers=headers)
                response.raise_for_status()
        return f"{self._supabase_url}/storage/v1/object/public/{self._bucket}/{clean_key}"

    async def delete(self, key: str) -> None:
        clean_key = key.lstrip("/")
        url = f"{self._supabase_url}/storage/v1/object/{self._bucket}/{clean_key}"
        headers = self._headers()
        if self._client is not None:
            response = await self._client.delete(url, headers=headers)
            if response.status_code not in (200, 204, 404):
                response.raise_for_status()
        else:
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=headers)
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
    return LocalDiskAttachmentStorage(
        storage_dir=cfg.attachments_storage_dir,
        public_base_url=f"{cfg.api_base_url}/attachments",
    )
