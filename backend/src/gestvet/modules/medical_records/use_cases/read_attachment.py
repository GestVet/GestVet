"""Caso de uso: entregar el archivo de un adjunto de la historia clínica.

Aplica el mismo recorte que la lectura de la historia: el personal ve el de
cualquier mascota, un cliente solo el de las suyas. El archivo nunca queda
publicado en el almacenamiento, así que este es el único camino para leerlo.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.modules.medical_records.domain.attachment import Attachment
from gestvet.modules.medical_records.domain.exceptions import AttachmentNotFound
from gestvet.modules.medical_records.ports.attachment_repository import AttachmentRepository
from gestvet.modules.medical_records.ports.attachment_storage import AttachmentStorage
from gestvet.modules.medical_records.ports.clinical_entry_repository import (
    ClinicalEntryRepository,
)
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory


@dataclass(frozen=True, slots=True)
class AttachmentFile:
    attachment: Attachment
    content: bytes


class ReadAttachment:
    def __init__(
        self,
        attachments: AttachmentRepository,
        storage: AttachmentStorage,
        entries: ClinicalEntryRepository,
        pets: PetDirectory,
    ) -> None:
        self._attachments = attachments
        self._storage = storage
        self._entries = entries
        self._pets = pets

    async def __call__(
        self, attachment_id: int, *, requester_id: int, is_staff: bool
    ) -> AttachmentFile:
        attachment = await self._attachments.get(attachment_id)
        if attachment is None:
            raise AttachmentNotFound(attachment_id)
        if not is_staff:
            entry = await self._entries.get(attachment.clinical_entry_id)
            # Un adjunto ajeno responde "no existe" y no "no puedes": responder
            # distinto confirmaría que ese identificador pertenece a alguien.
            if entry is None or not await self._pets.is_owned_by(entry.pet_id, requester_id):
                raise AttachmentNotFound(attachment_id)
        try:
            content = await self._storage.read(attachment.storage_key)
        except FileNotFoundError as error:
            raise AttachmentNotFound(attachment_id) from error
        return AttachmentFile(attachment=attachment, content=content)
