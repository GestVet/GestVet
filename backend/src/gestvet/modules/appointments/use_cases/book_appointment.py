"""Caso de uso: reservar una cita.

Concentra las tres comprobaciones que el original repartía entre dos consultas
SQL enormes y un par de `if` sueltos en el controlador.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.appointments.domain.entities import (
    ACTIVE_STATUSES,
    Appointment,
    AppointmentType,
    clinic_day_window,
)
from gestvet.modules.appointments.domain.exceptions import (
    AppointmentTypeNotFound,
    InvalidAppointment,
    OutsideAvailability,
    OverlappingAppointment,
    PetNotOwned,
    VeterinarianUnavailable,
)
from gestvet.modules.appointments.ports.repositories import (
    AppointmentQuery,
    AppointmentRepository,
    AppointmentTypeRepository,
    PetDirectory,
    ScheduleDirectory,
)


@dataclass(frozen=True, slots=True)
class BookAppointmentCommand:
    client_id: int
    pet_id: int
    veterinarian_id: int
    appointment_type_id: int
    scheduled_at: datetime
    description: str = ""


class BookAppointment:
    def __init__(
        self,
        appointments: AppointmentRepository,
        types: AppointmentTypeRepository,
        pets: PetDirectory,
        schedule: ScheduleDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._appointments = appointments
        self._types = types
        self._pets = pets
        self._schedule = schedule
        self._activity = activity

    async def __call__(self, command: BookAppointmentCommand) -> Appointment:
        appointment_type = await self._require_bookable_type(command.appointment_type_id)

        # La mascota tiene que ser del cliente que reserva. El original recibía
        # el identificador del cliente en el cuerpo y no comprobaba nada.
        if not await self._pets.is_owned_by(command.pet_id, command.client_id):
            raise PetNotOwned(command.pet_id)

        # El de guardia solo recibe emergencias. El original filtraba esto en
        # el listado; acá también se exige del lado servidor.
        if not await self._schedule.is_bookable_for_normal_appointments(command.veterinarian_id):
            raise VeterinarianUnavailable(
                "El veterinario elegido no está disponible para citas normales."
            )

        appointment = Appointment(
            scheduled_at=command.scheduled_at,
            duration=appointment_type.duration,
            client_id=command.client_id,
            pet_id=command.pet_id,
            veterinarian_id=command.veterinarian_id,
            appointment_type_id=appointment_type.id or 0,
            description=command.description,
        )

        await self._require_free_slot(appointment)
        await self._require_not_covering_emergency(appointment)
        reservada = await self._appointments.add(appointment)
        await self._activity.record(
            command.client_id, ActivityKind.APPOINTMENT_BOOKED, appointment_type.name
        )
        return reservada

    async def _require_bookable_type(self, type_id: int) -> AppointmentType:
        appointment_type = await self._types.get(type_id)
        if appointment_type is None or not appointment_type.is_active:
            raise AppointmentTypeNotFound(type_id)
        if appointment_type.is_emergency:
            # Una emergencia no se agenda: se abre en el momento y el sistema
            # elige al veterinario de guardia.
            raise InvalidAppointment(
                "Una emergencia no se reserva con antelación. Usá el alta de emergencia."
            )
        return appointment_type

    async def _require_free_slot(self, appointment: Appointment) -> None:
        # La cita entera, margen incluido, tiene que caber en un tramo
        # publicado por el veterinario.
        if not await self._schedule.covers(
            appointment.veterinarian_id, appointment.scheduled_at, appointment.ends_at
        ):
            raise OutsideAvailability()

        # Y no puede pisar otra cita activa del mismo veterinario. El margen
        # lo aplica la entidad, así que acá va la ventana tal cual.
        conflicts = await self._appointments.find_conflicting(
            appointment.veterinarian_id, appointment.scheduled_at, appointment.ends_at
        )
        if conflicts:
            raise OverlappingAppointment()

    async def _require_not_covering_emergency(self, appointment: Appointment) -> None:
        """Un respaldo con una emergencia activa no recibe citas normales ese día.

        Solo se activa para un veterinario normal que además está cubriendo:
        el de guardia dedicado ya está excluido del selector por su rol.
        """
        day_start, day_end = clinic_day_window(appointment.scheduled_at)
        cubriendo = await self._appointments.search(
            AppointmentQuery(
                veterinarian_id=appointment.veterinarian_id,
                is_emergency=True,
                statuses=ACTIVE_STATUSES,
                starts_after=day_start,
                ends_before=day_end,
                limit=1,
            )
        )
        if cubriendo.total > 0:
            raise VeterinarianUnavailable(
                "El veterinario está cubriendo una emergencia y no recibe citas normales hoy."
            )
