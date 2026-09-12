"""Caso de uso: consultar reclamos.

Un cliente ve solo los suyos; el personal, cualquiera -para eso los presenta
el cliente, para que administración los vea-.
"""

from __future__ import annotations

from dataclasses import replace

from gestvet.core.identity import Principal, Role
from gestvet.core.pagination import Page
from gestvet.modules.complaints.domain.entities import Complaint
from gestvet.modules.complaints.ports.complaint_repository import (
    ComplaintQuery,
    ComplaintRepository,
)


def scope_to(principal: Principal, query: ComplaintQuery) -> ComplaintQuery:
    if principal.role is Role.CLIENT:
        return replace(query, client_id=principal.user_id)
    return query


class ListComplaints:
    def __init__(self, complaints: ComplaintRepository) -> None:
        self._complaints = complaints

    async def __call__(self, query: ComplaintQuery) -> Page[Complaint]:
        return await self._complaints.search(query)
