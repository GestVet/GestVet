"""Registro de identidad de personas (DNI): el puerto.

Responde una sola pregunta: a quién pertenece un DNI. De lo que devuelva el
proveedor se usan solo los nombres y los apellidos; la dirección, el ubigeo o
cualquier otro dato se descarta en el adaptador, porque la clínica no lo
necesita y guardarlo sería tratar datos personales sin motivo (Ley 29733).

La única fuente prevista es RENIEC (`dni_reniec`). Consultarla exige un
convenio que la clínica todavía no tiene, así que hoy la verificación está
apagada. Cuando exista, el adaptador de RENIEC satisface este puerto y ningún
caso de uso cambia.

Python puro: lo importan los casos de uso.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class IdentityRegistryUnavailable(Exception):
    """La consulta no está configurada o el proveedor no respondió."""


@dataclass(frozen=True, slots=True)
class PersonName:
    first_names: str
    paternal_surname: str
    maternal_surname: str

    @property
    def last_names(self) -> str:
        return f"{self.paternal_surname} {self.maternal_surname}".strip()


class IdentityRegistry(Protocol):
    @property
    def available(self) -> bool:
        """Si la verificación está en uso: sin ella no se pide autorización para consultar."""
        ...

    async def lookup(self, document_id: str) -> PersonName | None:
        """Los nombres del DNI, o `None` si el DNI no existe."""
        ...


class DisabledIdentityRegistry:
    """Sin proveedor configurado: la consulta no está disponible y nada se bloquea por eso."""

    @property
    def available(self) -> bool:
        return False

    async def lookup(self, document_id: str) -> PersonName | None:
        raise IdentityRegistryUnavailable(
            "La consulta de DNI no está configurada en este servidor."
        )
