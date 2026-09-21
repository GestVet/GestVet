"""Caso de uso: adjuntar evidencia a un reclamo propio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from gestvet.modules.complaints.domain.evidence import ComplaintEvidence
from gestvet.modules.complaints.domain.exceptions import ComplaintNotFound
from gestvet.modules.complaints.ports.complaint_repository import ComplaintRepository
from gestvet.modules.complaints.ports.evidence_repository import EvidenceRepository
from gestvet.modules.complaints.ports.evidence_storage import EvidenceStorage


@dataclass(frozen=True, slots=True)
class UploadEvidenceCommand:
    complaint_id: int
    requester_id: int
    filename: str
    content_type: str
    content: bytes


class UploadEvidence:
    def __init__(
        self,
        evidence: EvidenceRepository,
        storage: EvidenceStorage,
        complaints: ComplaintRepository,
    ) -> None:
        self._evidence = evidence
        self._storage = storage
        self._complaints = complaints

    async def __call__(self, command: UploadEvidenceCommand) -> ComplaintEvidence:
        complaint = await self._complaints.get(command.complaint_id)
        # Misma respuesta para "no existe" y "no es tuyo": distinguirlas
        # confirmaría que el identificador pertenece a alguien.
        if complaint is None or complaint.client_id != command.requester_id:
            raise ComplaintNotFound(command.complaint_id)

        draft = ComplaintEvidence(
            complaint_id=command.complaint_id,
            filename=command.filename,
            content_type=command.content_type,
            size_bytes=len(command.content),
            storage_key=_storage_key(command.complaint_id, command.filename),
            uploaded_by=command.requester_id,
        )
        await self._storage.save(draft.storage_key, command.content, command.content_type)
        return await self._evidence.add(draft)


def _storage_key(complaint_id: int, filename: str) -> str:
    extension = "".join(char for char in filename.rsplit(".", 1)[-1] if char.isalnum())[:10]
    suffix = f".{extension}" if "." in filename and extension else ""
    return f"complaints/{complaint_id}/{uuid.uuid4().hex}{suffix}"
