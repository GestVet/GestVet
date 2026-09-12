"""Caso de uso: adjuntar un archivo a una entrada de la historia clínica."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.medical_records.domain.attachment import Attachment
from gestvet.modules.medical_records.domain.exceptions import ClinicalEntryNotFound
from gestvet.modules.medical_records.ports.attachment_repository import AttachmentRepository
from gestvet.modules.medical_records.ports.attachment_storage import AttachmentStorage
from gestvet.modules.medical_records.ports.clinical_entry_repository import (
    ClinicalEntryRepository,
)


@dataclass(frozen=True, slots=True)
class UploadAttachmentCommand:
    clinical_entry_id: int
    filename: str
    content_type: str
    content: bytes
    uploaded_by: int


class UploadAttachment:
    def __init__(
        self,
        attachments: AttachmentRepository,
        storage: AttachmentStorage,
        entries: ClinicalEntryRepository,
        activity: ActivityRecorder,
    ) -> None:
        self._attachments = attachments
        self._storage = storage
        self._entries = entries
        self._activity = activity

    async def __call__(self, command: UploadAttachmentCommand) -> Attachment:
        entry = await self._entries.get(command.clinical_entry_id)
        if entry is None:
            raise ClinicalEntryNotFound(command.clinical_entry_id)

        # Se valida antes de tocar el almacenamiento: un archivo rechazado no
        # debe llegar a escribirse en ningún lado.
        draft = Attachment(
            clinical_entry_id=command.clinical_entry_id,
            filename=command.filename,
            content_type=command.content_type,
            size_bytes=len(command.content),
            storage_key=_storage_key(command.clinical_entry_id, command.filename),
            uploaded_by=command.uploaded_by,
        )

        draft.url = await self._storage.save(
            draft.storage_key, command.content, command.content_type
        )
        guardado = await self._attachments.add(draft)
        await self._activity.record(
            command.uploaded_by, ActivityKind.ATTACHMENT_UPLOADED, guardado.filename
        )
        return guardado


def _storage_key(clinical_entry_id: int, filename: str) -> str:
    extension = "".join(char for char in filename.rsplit(".", 1)[-1] if char.isalnum())[:10]
    suffix = f".{extension}" if "." in filename and extension else ""
    return f"clinical-entries/{clinical_entry_id}/{uuid.uuid4().hex}{suffix}"
