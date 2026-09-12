"""Puerto de persistencia de los adjuntos.

Guarda solo la referencia (nombre, tipo, tamaño, URL): el archivo en sí lo
guarda `AttachmentStorage`.
"""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.medical_records.domain.attachment import Attachment


class AttachmentRepository(Protocol):
    async def add(self, attachment: Attachment) -> Attachment: ...

    async def get(self, attachment_id: int) -> Attachment | None: ...

    async def list_for_entry(self, clinical_entry_id: int) -> list[Attachment]: ...

    async def delete(self, attachment_id: int) -> None: ...
