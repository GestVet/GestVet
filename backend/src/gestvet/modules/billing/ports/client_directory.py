"""Puerto de lectura hacia `accounts`.

Solo lo que hace falta para avisar por WhatsApp que un pago se confirmó: el
nombre y el teléfono. Nada de esto lo posee `billing`; se lee de la tabla
ajena.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ClientContact:
    name: str
    phone: str


class ClientDirectory(Protocol):
    async def find_contact(self, client_id: int) -> ClientContact | None: ...
