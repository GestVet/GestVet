"""Puerto de almacenamiento de la evidencia de un reclamo.

Misma forma que `AttachmentStorage` de `medical_records`, a propósito: los
dos los satisface el mismo adaptador genérico (`core.attachments`), sin que
ninguno de los dos módulos tenga que importar al otro.
"""

from __future__ import annotations

from typing import Protocol


class EvidenceStorage(Protocol):
    async def save(self, key: str, content: bytes, content_type: str) -> str: ...

    async def delete(self, key: str) -> None: ...
