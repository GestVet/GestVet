"""Puerto de almacenamiento de archivos.

El caso de uso guarda bytes bajo una clave y no sabe si terminan en disco
local, en un bucket S3-compatible o en cualquier otro proveedor: eso lo
decide el adaptador. Separado de `AttachmentRepository` porque uno guarda el
archivo y el otro guarda la referencia, y son responsabilidades distintas.
"""

from __future__ import annotations

from typing import Protocol


class AttachmentStorage(Protocol):
    async def save(self, key: str, content: bytes, content_type: str) -> str:
        """Guarda el archivo y devuelve la URL desde la que se puede leer."""
        ...

    async def delete(self, key: str) -> None: ...
