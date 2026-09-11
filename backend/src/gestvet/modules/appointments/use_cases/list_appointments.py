"""Caso de uso: listar citas.

El listado se acota por participante antes de tocar la base. El original tenía
una consulta distinta por rol, cada una con sus propios `JOIN` repetidos; acá
hay un solo criterio de búsqueda y el rol decide cómo se rellena.
"""

from __future__ import annotations

from gestvet.core.identity import Principal, Role
from gestvet.core.pagination import Page
from gestvet.modules.appointments.domain.entities import Appointment
from gestvet.modules.appointments.ports.repositories import AppointmentQuery, AppointmentRepository


class ListAppointments:
    def __init__(self, appointments: AppointmentRepository) -> None:
        self._appointments = appointments

    async def __call__(self, query: AppointmentQuery) -> Page[Appointment]:
        return await self._appointments.search(query)


def scope_to(principal: Principal, query: AppointmentQuery) -> AppointmentQuery:
    """Recorta la búsqueda a lo que este usuario tiene derecho a ver.

    Se aplica sobre el criterio, no sobre el resultado: un filtro que llega del
    cliente nunca puede ampliar el conjunto, solo estrecharlo.
    """
    if principal.role is Role.ADMIN:
        return query
    if principal.role is Role.CLIENT:
        return replace_participant(query, client_id=principal.user_id)
    return replace_participant(query, veterinarian_id=principal.user_id)


def replace_participant(
    query: AppointmentQuery,
    client_id: int | None = None,
    veterinarian_id: int | None = None,
) -> AppointmentQuery:
    return AppointmentQuery(
        client_id=client_id if client_id is not None else query.client_id,
        veterinarian_id=(veterinarian_id if veterinarian_id is not None else query.veterinarian_id),
        pet_id=query.pet_id,
        statuses=query.statuses,
        is_emergency=query.is_emergency,
        starts_after=query.starts_after,
        ends_before=query.ends_before,
        limit=query.limit,
        offset=query.offset,
    )
