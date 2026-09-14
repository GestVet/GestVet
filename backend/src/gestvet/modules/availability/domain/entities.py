"""Entidades de dominio de la agenda.

Un turno es una ventana en la que un veterinario trabaja para la clínica. Lo
asigna la administración, como se hace en las clínicas de Trujillo con atención
de día y guardia de noche: el veterinario ve sus turnos y, si uno no le sirve,
pide un cambio. Python puro: sin FastAPI, sin SQLAlchemy, sin Pydantic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from gestvet.core.clinic_time import clinic_date
from gestvet.modules.availability.domain.exceptions import (
    ChangeRequestAlreadyResolved,
    InvalidChangeRequest,
    InvalidSlot,
)

MIN_SLOT_DURATION = timedelta(minutes=15)
MAX_REGULAR_DURATION = timedelta(hours=12)
# Una guardia puede cubrir el día entero: en una clínica con emergencias las 24
# horas es el turno que se reparte.
MAX_ON_CALL_DURATION = timedelta(hours=24)
# Hasta dónde se planifica. Un año alcanza para cualquier rotación y evita que un
# error de tipeo deje un turno en el año 3000.
SCHEDULING_HORIZON = timedelta(days=365)

MIN_MESSAGE_LENGTH = 5
MAX_MESSAGE_LENGTH = 500


class ShiftKind(StrEnum):
    # En un turno de atención se reciben citas.
    REGULAR = "regular"
    # En una guardia se cubren las emergencias; no se ofrece para reservar.
    ON_CALL = "on_call"

    @property
    def label(self) -> str:
        return "Guardia" if self is ShiftKind.ON_CALL else "Atención"


@dataclass(slots=True)
class AvailabilitySlot:
    veterinarian_id: int
    starts_at: datetime
    ends_at: datetime
    kind: ShiftKind = ShiftKind.REGULAR
    # Quién lo asignó. Vacío en los turnos anteriores a que los asignara la clínica.
    assigned_by: int | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.starts_at = _require_utc(self.starts_at, "hora de inicio")
        self.ends_at = _require_utc(self.ends_at, "hora de fin")
        if self.ends_at <= self.starts_at:
            raise InvalidSlot("La hora de fin debe ser posterior a la de inicio.")
        if self.duration < MIN_SLOT_DURATION:
            raise InvalidSlot("Un turno debe durar al menos 15 minutos.")
        self._require_fitting_length()

    def _require_fitting_length(self) -> None:
        if self.kind is ShiftKind.ON_CALL:
            if self.duration > MAX_ON_CALL_DURATION:
                raise InvalidSlot("Una guardia no puede superar las 24 horas.")
            return
        if self.duration > MAX_REGULAR_DURATION:
            raise InvalidSlot(
                "Un turno de atención no puede superar las 12 horas. "
                "Divídelo en dos o asigna una guardia."
            )
        # La noche la cubre la guardia: un turno de atención no cruza la medianoche.
        if clinic_date(self.starts_at) != clinic_date(self.ends_at - timedelta(microseconds=1)):
            raise InvalidSlot(
                "Un turno de atención empieza y termina el mismo día. "
                "Para cubrir la noche, asigna una guardia."
            )

    @property
    def duration(self) -> timedelta:
        return self.ends_at - self.starts_at

    def overlaps(self, other: AvailabilitySlot) -> bool:
        """Dos turnos se tocan si uno empieza antes de que el otro termine.

        Compartir el extremo no es superponerse: un turno que termina a las 12
        y otro que empieza a las 12 son contiguos, no simultáneos.
        """
        return self.starts_at < other.ends_at and other.starts_at < self.ends_at

    def covers(self, starts_at: datetime, ends_at: datetime) -> bool:
        """La ventana pedida cabe entera dentro del turno."""
        return self.starts_at <= starts_at and ends_at <= self.ends_at

    def belongs_to(self, veterinarian_id: int) -> bool:
        return self.veterinarian_id == veterinarian_id


def ensure_schedulable(slot: AvailabilitySlot, now: datetime) -> None:
    """Un turno nuevo es de hoy en adelante y dentro del próximo año.

    Hoy cuenta entero: la administración puede cargar a primera hora el turno
    que ya empezó. Lo que no tiene sentido es asignar uno que ya terminó.
    """
    if slot.ends_at <= now:
        raise InvalidSlot("Ese turno ya terminó. Asigna turnos de hoy en adelante.")
    if clinic_date(slot.starts_at) < clinic_date(now):
        raise InvalidSlot("El turno empieza en un día que ya pasó.")
    if slot.starts_at > now + SCHEDULING_HORIZON:
        raise InvalidSlot("Solo se asignan turnos hasta un año adelante.")


class ChangeRequestStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(slots=True)
class ShiftChangeRequest:
    """Un veterinario pide cambiar un turno; la administración responde.

    Aceptar no mueve el turno solo: quien administra lo reasigna a mano, porque
    un cambio suele necesitar a otro veterinario que lo cubra.
    """

    veterinarian_id: int
    message: str
    slot_id: int | None = None
    status: ChangeRequestStatus = ChangeRequestStatus.PENDING
    response: str = ""
    resolved_by: int | None = None
    resolved_at: datetime | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.message = self.message.strip()
        if not MIN_MESSAGE_LENGTH <= len(self.message) <= MAX_MESSAGE_LENGTH:
            raise InvalidChangeRequest(
                f"Cuenta qué necesitas cambiar en {MIN_MESSAGE_LENGTH} a "
                f"{MAX_MESSAGE_LENGTH} caracteres."
            )
        self.response = self.response.strip()

    def resolve(self, actor_id: int, accepted: bool, response: str, now: datetime) -> None:
        if self.status is not ChangeRequestStatus.PENDING:
            raise ChangeRequestAlreadyResolved()
        respuesta = response.strip()
        if len(respuesta) > MAX_MESSAGE_LENGTH:
            raise InvalidChangeRequest(
                f"La respuesta puede tener hasta {MAX_MESSAGE_LENGTH} caracteres."
            )
        self.status = ChangeRequestStatus.ACCEPTED if accepted else ChangeRequestStatus.REJECTED
        self.response = respuesta
        self.resolved_by = actor_id
        self.resolved_at = now


def _require_utc(moment: datetime, field_name: str) -> datetime:
    """Exige una fecha con zona y la normaliza a UTC.

    Una marca sin zona es ambigua, y la ambigüedad en una agenda se paga con
    citas a la hora equivocada.
    """
    if moment.tzinfo is None:
        raise InvalidSlot(f"La {field_name} debe traer zona horaria.")
    return moment.astimezone(UTC)
