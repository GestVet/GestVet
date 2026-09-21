"""Caso de uso: entregar el archivo de la evidencia de un reclamo.

Lo ve quien presentó el reclamo o el personal que los atiende, igual que el
listado. El archivo nunca queda publicado en el almacenamiento, así que este
es el único camino para leerlo.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.modules.complaints.domain.evidence import ComplaintEvidence
from gestvet.modules.complaints.domain.exceptions import EvidenceNotFound
from gestvet.modules.complaints.ports.complaint_repository import ComplaintRepository
from gestvet.modules.complaints.ports.evidence_repository import EvidenceRepository
from gestvet.modules.complaints.ports.evidence_storage import EvidenceStorage


@dataclass(frozen=True, slots=True)
class EvidenceFile:
    evidence: ComplaintEvidence
    content: bytes


class ReadEvidence:
    def __init__(
        self,
        evidence: EvidenceRepository,
        storage: EvidenceStorage,
        complaints: ComplaintRepository,
    ) -> None:
        self._evidence = evidence
        self._storage = storage
        self._complaints = complaints

    async def __call__(
        self, evidence_id: int, *, requester_id: int, only_own: bool
    ) -> EvidenceFile:
        evidence = await self._evidence.get(evidence_id)
        if evidence is None:
            raise EvidenceNotFound(evidence_id)
        if only_own:
            complaint = await self._complaints.get(evidence.complaint_id)
            # Misma respuesta para "no existe" y "no es tuya".
            if complaint is None or complaint.client_id != requester_id:
                raise EvidenceNotFound(evidence_id)
        try:
            content = await self._storage.read(evidence.storage_key)
        except FileNotFoundError as error:
            raise EvidenceNotFound(evidence_id) from error
        return EvidenceFile(evidence=evidence, content=content)
