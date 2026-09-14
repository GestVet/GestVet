"""Caso de uso: completar nombre y apellido desde el DNI, en el alta exprés.

Lo usa el personal cuando llega alguien sin cuenta a una emergencia: evita
tipear mal el nombre con apuro. Solo devuelve nombres y apellidos, y cada
consulta queda en la bitácora con quién la hizo, porque consultar un DNI es
tratar un dato personal de un tercero.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity_registry import IdentityRegistry, PersonName
from gestvet.modules.accounts.domain.entities import validate_document_id
from gestvet.modules.accounts.domain.exceptions import (
    DocumentIdRequired,
    DocumentNotFoundInRegistry,
)

_VISIBLE_DIGITS = 3


@dataclass(frozen=True, slots=True)
class LookUpDocumentCommand:
    actor_id: int
    document_id: str


class LookUpDocument:
    def __init__(self, registry: IdentityRegistry, activity: ActivityRecorder) -> None:
        self._registry = registry
        self._activity = activity

    async def __call__(self, command: LookUpDocumentCommand) -> PersonName:
        document_id = validate_document_id(command.document_id)
        if not document_id:
            raise DocumentIdRequired()

        person = await self._registry.lookup(document_id)
        # En la bitácora va enmascarado: alcanza para auditar sin repetir el DNI.
        await self._activity.record(
            command.actor_id,
            ActivityKind.DOCUMENT_LOOKED_UP,
            f"DNI terminado en {document_id[-_VISIBLE_DIGITS:]}",
        )
        if person is None:
            raise DocumentNotFoundInRegistry()
        return person
