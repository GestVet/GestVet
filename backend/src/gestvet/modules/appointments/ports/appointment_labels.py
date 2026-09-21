"""Puerto de lectura: con qué nombre se muestra una cita.

Una cita guarda a la mascota, al cliente y al veterinario por identificador,
y la pantalla necesita sus nombres. Esos datos son de `pets` y `accounts`,
módulos que este no puede importar: la pregunta se declara acá y un adaptador
la responde leyendo las tablas ajenas.

Se pide para una página entera de una vez: una consulta por cita sería una
por fila del listado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AppointmentLabels:
    pet_name: str
    client_name: str
    veterinarian_name: str
    appointment_type_name: str
    is_emergency: bool


class AppointmentLabelDirectory(Protocol):
    async def labels_for(self, appointment_ids: list[int]) -> dict[int, AppointmentLabels]:
        """Los nombres de cada cita pedida; una que no existe no figura."""
        ...
