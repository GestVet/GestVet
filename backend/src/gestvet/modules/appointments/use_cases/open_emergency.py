"""Caso de uso: abrir una cita de emergencia.

El cliente no elige veterinario ni hora: la emergencia es ahora y el sistema
asigna al que esté de guardia. Es la misma idea del original, con la diferencia
de que allá vivía dentro de una consulta SQL de treinta líneas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.clinic_time import clinic_day_window
from gestvet.modules.appointments.domain.entities import ACTIVE_STATUSES, Appointment
from gestvet.modules.appointments.domain.exceptions import (
    AppointmentTypeNotFound,
    NoEmergencyVeterinarian,
    PetNotOwned,
)
from gestvet.modules.appointments.domain.risk_consent import ensure_risk_consent_usable
from gestvet.modules.appointments.ports.repositories import (
    AppointmentQuery,
    AppointmentRepository,
    AppointmentTypeRepository,
    PetDirectory,
    ScheduleDirectory,
)
from gestvet.modules.appointments.ports.risk_consent_directory import RiskConsentDirectory


@dataclass(frozen=True, slots=True)
class OpenEmergencyCommand:
    client_id: int
    pet_id: int
    risk_consent_id: int
    description: str = ""


class OpenEmergency:
    def __init__(
        self,
        appointments: AppointmentRepository,
        types: AppointmentTypeRepository,
        pets: PetDirectory,
        schedule: ScheduleDirectory,
        consents: RiskConsentDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._appointments = appointments
        self._types = types
        self._pets = pets
        self._schedule = schedule
        self._consents = consents
        self._activity = activity

    async def __call__(self, command: OpenEmergencyCommand) -> Appointment:
        emergency_type = await self._types.get_emergency()
        if emergency_type is None:
            raise AppointmentTypeNotFound(0)

        if not await self._pets.is_owned_by(command.pet_id, command.client_id):
            raise PetNotOwned(command.pet_id)

        now = datetime.now(UTC)
        # Lo único que se le pide al dueño antes de atender: saber que el
        # animal puede estar grave y que el costo se conoce al final. Nada más
        # frena una emergencia.
        ensure_risk_consent_usable(
            await self._consents.find(command.risk_consent_id),
            client_id=command.client_id,
            pet_id=command.pet_id,
            now=now,
        )
        veterinarian_id = await self._pick_veterinarian(now)

        abierta = await self._appointments.add(
            Appointment(
                scheduled_at=now,
                duration=emergency_type.duration,
                client_id=command.client_id,
                pet_id=command.pet_id,
                veterinarian_id=veterinarian_id,
                appointment_type_id=emergency_type.id or 0,
                description=command.description or "Cita de emergencia",
                risk_consent_id=command.risk_consent_id,
            )
        )
        await self._activity.record(command.client_id, ActivityKind.EMERGENCY_OPENED)
        return abierta

    async def _pick_veterinarian(self, moment: datetime) -> int:
        # Entre los de guardia gana el menos cargado. El original ordenaba por
        # la misma cuenta, pero además descartaba a cualquiera que tuviera una
        # cita activa, así que con la clínica llena no asignaba a nadie.
        on_duty = await self._schedule.veterinarians_on_duty(moment)
        menos_cargado: int | None = None
        if on_duty:
            loads = [
                (await self._appointments.count_active_for(vet_id), vet_id) for vet_id in on_duty
            ]
            carga_minima, menos_cargado = min(loads)
            if carga_minima == 0:
                return menos_cargado

        # Todos los de guardia ya atienden algo, o nadie está de guardia a esta
        # hora: cubre un veterinario en su turno de atención que tenga libre el
        # resto de la jornada, antes que sobrecargar a uno solo.
        libre = await self._pick_free_on_shift(moment, frozenset(on_duty))
        if libre is not None:
            return libre

        if menos_cargado is not None:
            return menos_cargado

        raise NoEmergencyVeterinarian()

    async def _pick_free_on_shift(self, moment: datetime, on_duty: frozenset[int]) -> int | None:
        candidatos = [
            vet_id
            for vet_id in await self._schedule.veterinarians_working(moment)
            if vet_id not in on_duty
        ]
        _, fin_de_jornada = clinic_day_window(moment)
        for candidato_id in candidatos:
            pagina = await self._appointments.search(
                AppointmentQuery(
                    veterinarian_id=candidato_id,
                    statuses=ACTIVE_STATUSES,
                    starts_after=moment,
                    ends_before=fin_de_jornada,
                    limit=1,
                )
            )
            if pagina.total == 0:
                return candidato_id
        return None
