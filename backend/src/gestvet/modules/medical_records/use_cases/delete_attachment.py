"""Caso de uso: quitar un adjunto de la historia clínica."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.medical_records.domain.exceptions import AttachmentNotFound
from gestvet.modules.medical_records.ports.attachment_repository import AttachmentRepository
from gestvet.modules.medical_records.ports.attachment_storage import AttachmentStorage


@dataclass(frozen=True, slots=True)
class DeleteAttachmentCommand:
    attachment_id: int
    requested_by: int


class DeleteAttachment:
    def __init__(
        self,
        attachments: AttachmentRepository,
        storage: AttachmentStorage,
        activity: ActivityRecorder,
    ) -> None:
        self._attachments = attachments
        self._storage = storage
        self._activity = activity

    async def __call__(self, command: DeleteAttachmentCommand) -> None:
        attachment = await self._attachments.get(command.attachment_id)
        if attachment is None:
            raise AttachmentNotFound(command.attachment_id)

        await self._storage.delete(attachment.storage_key)
        await self._attachments.delete(command.attachment_id)
        await self._activity.record(
            command.requested_by, ActivityKind.ATTACHMENT_DELETED, attachment.filename
        )
