"""Avisos en tiempo real, sin tecnología.

Un aviso dice qué cambió y a quién le importa, nunca los datos: el navegador que
lo recibe vuelve a pedirlos por la API, y así la regla de quién puede ver qué
sigue viviendo en un solo lugar. Por eso alcanza con el tema, las cuentas
destinatarias y los roles que ven todo.

El envío concreto (en memoria, o repartido por Postgres entre procesos) es un
adaptador: vive en `realtime_broker` y este módulo no lo conoce.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from gestvet.core.identity import Principal, Role

APPOINTMENTS_TOPIC = "appointments"
# Cambiaron los permisos de la cuenta: la interfaz vuelve a pedirlos.
PERMISSIONS_TOPIC = "permissions"
# Cambiaron turnos o pedidos de cambio: la agenda se vuelve a pedir.
SCHEDULE_TOPIC = "schedule"
# Cambió el catálogo de especies y razas: los formularios vuelven a pedirlo.
PET_CATALOG_TOPIC = "pet-catalog"
# Se pidió, respondió o registró un consentimiento: el dueño ve el pedido y el
# veterinario la respuesta sin recargar.
CONSENTS_TOPIC = "consents"


@dataclass(frozen=True, slots=True)
class RealtimeEvent:
    topic: str
    user_ids: frozenset[int] = field(default_factory=frozenset)
    # Roles que reciben el aviso aunque no participen, como la administración,
    # que ve todas las citas.
    roles: frozenset[Role] = field(default_factory=frozenset)
    reference_id: int | None = None

    def is_for(self, principal: Principal) -> bool:
        return principal.user_id in self.user_ids or principal.role in self.roles


class EventPublisher(Protocol):
    def publish(self, event: RealtimeEvent) -> None:
        """Encola el aviso; sale recién si la transacción en curso se confirma."""
