"""Entidades de dominio de citas.

Python puro. Las relaciones con clientes, mascotas y veterinarios se guardan
por identificador: cada uno vive en otro módulo y este no puede importarlo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum

from gestvet.modules.appointments.domain.exceptions import IllegalStatusChange, InvalidAppointment

# Margen entre dos citas del mismo veterinario. Viene del sistema original y
# existe para que una consulta que se estira no arrastre a la siguiente.
TURNAROUND = timedelta(minutes=10)

# Techo de duración de una cita. Existe por dos razones: una consulta más larga
# es un error de carga, y acota la ventana de candidatos que hay que revisar
# para detectar un solapamiento.
MAX_APPOINTMENT_DURATION = timedelta(hours=8)

MAX_DESCRIPTION_LENGTH = 500
MAX_REASON_LENGTH = 300

# La clínica opera en un único local, en Trujillo, sin horario de verano: el
# desplazamiento es un dato del negocio, no una preferencia de quien mira la
# pantalla, así que vive acá y no en el frontend pese a que el resto del
# sistema solo convierte fechas en la interfaz.
CLINIC_UTC_OFFSET = timedelta(hours=-5)


def clinic_day_window(moment: datetime) -> tuple[datetime, datetime]:
    """Ventana en UTC del día calendario de la clínica que contiene `moment`.

    Comparar fechas de calendario en UTC directamente rompe cerca de la
    medianoche: una cita de las 20:00 en Trujillo cae en el día siguiente en
    UTC, y "todo ese día" dejaría de incluirla.
    """
    local_wall_clock = moment + CLINIC_UTC_OFFSET
    local_midnight = datetime.combine(local_wall_clock.date(), time.min, tzinfo=UTC)
    starts_at = local_midnight - CLINIC_UTC_OFFSET
    return starts_at, starts_at + timedelta(days=1)


class AppointmentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]

    @property
    def is_final(self) -> bool:
        return self in _FINAL_STATUSES

    @property
    def blocks_the_agenda(self) -> bool:
        """Una cita cancelada libera el hueco; el resto lo sigue ocupando."""
        return self is not AppointmentStatus.CANCELLED


_STATUS_LABELS: dict[AppointmentStatus, str] = {
    AppointmentStatus.PENDING: "Pendiente",
    AppointmentStatus.CONFIRMED: "Confirmada",
    AppointmentStatus.COMPLETED: "Completada",
    AppointmentStatus.CANCELLED: "Cancelada",
    AppointmentStatus.NO_SHOW: "No asistió",
}

_FINAL_STATUSES = frozenset(
    {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}
)

# Cuánto se espera después de la hora de una cita antes de darla por no
# asistida sola, sin que nadie la haya cerrado. El margen evita marcar así una
# cita que el personal todavía no tuvo tiempo de completar.
NO_SHOW_GRACE = timedelta(hours=3)

# El original dejaba pasar cualquier estado a cualquier otro, así que una cita
# cancelada podía revivir como completada. Acá las transiciones son explícitas.
_ALLOWED_TRANSITIONS: dict[AppointmentStatus, frozenset[AppointmentStatus]] = {
    AppointmentStatus.PENDING: frozenset(
        {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}
    ),
    AppointmentStatus.CONFIRMED: frozenset(
        {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}
    ),
    AppointmentStatus.COMPLETED: frozenset(),
    AppointmentStatus.CANCELLED: frozenset(),
    AppointmentStatus.NO_SHOW: frozenset(),
}

# Estados que siguen ocupando la agenda del veterinario.
ACTIVE_STATUSES: frozenset[AppointmentStatus] = frozenset(
    status for status in AppointmentStatus if status.blocks_the_agenda
)


@dataclass(slots=True)
class AppointmentType:
    """Motivo de consulta, con su duración y su precio.

    El original marcaba la emergencia con el identificador 8, y ese número
    aparecía escrito a mano en media docena de consultas. Acá es una bandera.
    """

    name: str
    duration: timedelta
    price: Decimal
    is_emergency: bool = False
    is_active: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise InvalidAppointment("El tipo de cita necesita un nombre.")
        if self.duration <= timedelta(0):
            raise InvalidAppointment("La duración debe ser positiva.")
        if self.duration > MAX_APPOINTMENT_DURATION:
            raise InvalidAppointment(f"Una cita no puede durar más de {MAX_APPOINTMENT_DURATION}.")
        if self.price < 0:
            raise InvalidAppointment("El precio no puede ser negativo.")


@dataclass(slots=True)
class Appointment:
    scheduled_at: datetime
    duration: timedelta
    client_id: int
    pet_id: int
    veterinarian_id: int
    appointment_type_id: int
    description: str = ""
    status: AppointmentStatus = AppointmentStatus.PENDING
    cancellation_reason: str = ""
    updated_by: int | None = None
    # Cuándo se mandó el recordatorio de WhatsApp, para no mandarlo dos veces.
    # `None` significa "todavía no". No es un estado de la cita: convive con
    # cualquiera de los de arriba.
    reminder_sent_at: datetime | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.scheduled_at.tzinfo is None:
            raise InvalidAppointment("La fecha de la cita debe traer zona horaria.")
        self.scheduled_at = self.scheduled_at.astimezone(UTC)
        if self.duration <= timedelta(0):
            raise InvalidAppointment("La duración debe ser positiva.")
        self.description = _trim(self.description, "descripción", MAX_DESCRIPTION_LENGTH)
        self.cancellation_reason = _trim(
            self.cancellation_reason, "razón de cancelación", MAX_REASON_LENGTH
        )

    @property
    def ends_at(self) -> datetime:
        return self.scheduled_at + self.duration

    @property
    def blocked_until(self) -> datetime:
        """Hasta cuándo el veterinario sigue ocupado, margen incluido."""
        return self.ends_at + TURNAROUND

    def overlaps(self, starts_at: datetime, ends_at: datetime) -> bool:
        """Si esta cita choca con otra que ocupara la ventana dada.

        El margen cuenta a los dos lados: entre dos citas del mismo
        veterinario tiene que quedar ese hueco, venga la nueva antes o
        despues. Que la regla viva entera aca evita que cada consumidor
        tenga que acordarse de ensanchar la ventana por su cuenta.
        """
        return self.scheduled_at < ends_at + TURNAROUND and starts_at < self.blocked_until

    def confirm(self, actor_id: int) -> None:
        self._move_to(AppointmentStatus.CONFIRMED, actor_id)

    def complete(self, actor_id: int) -> None:
        self._move_to(AppointmentStatus.COMPLETED, actor_id)

    def mark_no_show(self, actor_id: int) -> None:
        self._move_to(AppointmentStatus.NO_SHOW, actor_id)

    def mark_reminder_sent(self, now: datetime | None = None) -> None:
        self.reminder_sent_at = now or datetime.now(UTC)

    def effective_status(self, now: datetime | None = None) -> AppointmentStatus:
        """El estado que corresponde en este instante.

        Una cita que sigue pendiente o confirmada mucho después de su hora,
        sin que nadie la haya cerrado, no deja de ser una inasistencia porque
        nadie volvió a mirarla: se calcula al leer, en vez de necesitar un
        trabajo en segundo plano que la marque. Ver `QrCharge.effective_status`
        para la misma idea aplicada a un cobro vencido.
        """
        reference = now or datetime.now(UTC)
        if (
            self.status in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)
            and reference >= self.ends_at + NO_SHOW_GRACE
        ):
            return AppointmentStatus.NO_SHOW
        return self.status

    def cancel(self, actor_id: int, reason: str) -> None:
        cleaned = _trim(reason, "razón de cancelación", MAX_REASON_LENGTH)
        if not cleaned:
            # Quien cancela le debe una explicación a la otra parte. El
            # original guardaba el campo pero nunca lo exigía.
            raise InvalidAppointment("Cancelar una cita exige indicar la razón.")
        self._move_to(AppointmentStatus.CANCELLED, actor_id)
        self.cancellation_reason = cleaned

    def involves(self, user_id: int) -> bool:
        return user_id in (self.client_id, self.veterinarian_id)

    def _move_to(self, target: AppointmentStatus, actor_id: int) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise IllegalStatusChange(self.status.label, target.label)
        self.status = target
        self.updated_by = actor_id


def _trim(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if len(value) > max_length:
        raise InvalidAppointment(f"La {field_name} admite {max_length} caracteres como máximo.")
    return value
