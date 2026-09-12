"""Puerto de persistencia de la evidencia de un reclamo."""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.complaints.domain.evidence import ComplaintEvidence


class EvidenceRepository(Protocol):
    async def add(self, evidence: ComplaintEvidence) -> ComplaintEvidence: ...

    async def list_for_complaint(self, complaint_id: int) -> list[ComplaintEvidence]: ...
