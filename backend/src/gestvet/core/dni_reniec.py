"""Consulta de DNI con RENIEC.

RENIEC es la única fuente prevista para verificar un DNI: un proveedor privado
no documenta de dónde saca los datos y el riesgo legal sería de la clínica
(Ley 29733). Consultar RENIEC exige un convenio con la entidad que la clínica
todavía no tiene, así que por ahora la verificación no está en uso: el registro
no pide autorización ni compara nombres, y el alta exprés de emergencia no
ofrece completar desde el DNI.

Cuando el convenio exista, acá va el adaptador que satisfaga `IdentityRegistry`
con el acceso que entregue RENIEC, y `get_identity_registry` lo devuelve en
lugar del registro apagado. Ningún caso de uso ni pantalla cambia: la interfaz
pregunta a `GET /auth/identity-check` si la verificación está en uso.
"""

from __future__ import annotations

from gestvet.core.identity_registry import DisabledIdentityRegistry, IdentityRegistry


def get_identity_registry() -> IdentityRegistry:
    return DisabledIdentityRegistry()
