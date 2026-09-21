"""Qué cita puede tocar el personal al pedir o registrar un consentimiento."""

from __future__ import annotations

from gestvet.core.identity import Principal, Role
from gestvet.modules.consents.domain.appointment_facts import AppointmentFacts, ensure_visible
from gestvet.modules.consents.ports.appointment_directory import AppointmentDirectory


async def appointment_for(
    appointments: AppointmentDirectory, appointment_id: int, principal: Principal
) -> AppointmentFacts:
    """La cita, si la atiende quien pregunta o si ve todas (la administración).

    Es el mismo recorte que aplica `appointments` al listar: el veterinario
    solo ve sus citas.
    """
    facts = await appointments.find(appointment_id)
    return ensure_visible(
        facts,
        appointment_id,
        user_id=principal.user_id,
        sees_all=principal.role is Role.ADMIN,
    )
