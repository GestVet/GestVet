"""Adaptador de almacenamiento de archivos.

Vive en el núcleo por la misma razón que `email.py`: no conoce ningún tipo de
negocio, solo recibe una clave y bytes. Satisface el puerto `AttachmentStorage`
de `medical_records` por estructura.

`LocalDiskAttachmentStorage` es el único adaptador hoy: guarda el archivo en
disco y lo sirve como archivo estático. Sirve para desarrollar y probar sin
depender de un proveedor real. En producción se reemplaza por un adaptador que
hable contra un bucket S3-compatible (Supabase Storage, Cloudflare R2, AWS S3),
sin tocar ningún caso de uso: el puerto no cambia.
"""

from __future__ import annotations

import asyncio
from pathlib import Path


class LocalDiskAttachmentStorage:
    def __init__(self, storage_dir: str, public_base_url: str) -> None:
        self._storage_dir = Path(storage_dir)
        self._public_base_url = public_base_url.rstrip("/")

    async def save(self, key: str, content: bytes, content_type: str) -> str:
        del content_type  # el disco no distingue tipos; lo hace el navegador al leerlo
        await asyncio.to_thread(self._write, key, content)
        return f"{self._public_base_url}/{key}"

    async def delete(self, key: str) -> None:
        await asyncio.to_thread((self._storage_dir / key).unlink, True)

    def _write(self, key: str, content: bytes) -> None:
        destination = self._storage_dir / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
