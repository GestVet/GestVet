"""Puerto de persistencia de reclamos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page
from gestvet.modules.complaints.domain.entities import Complaint


@dataclass(frozen=True, slots=True)
class ComplaintQuery:
    client_id: int | None = None
    veterinarian_id: int | None = None
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


class ComplaintRepository(Protocol):
    async def add(self, complaint: Complaint) -> Complaint: ...

    async def get(self, complaint_id: int) -> Complaint | None: ...

    async def search(self, query: ComplaintQuery) -> Page[Complaint]: ...
