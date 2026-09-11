"""Entidades de dominio de disponibilidad.

Un tramo es una ventana de tiempo en la que un veterinario atiende. Python
puro: sin FastAPI, sin SQLAlchemy, sin Pydantic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from gestvet.availability.domain.exceptions import InvalidSlot

MIN_SLOT_DURATION = timedelta(minutes=15)
MAX_SLOT_DURATION = timedelta(hours=12)


@dataclass(slots=True)
class AvailabilitySlot:
    veterinarian_id: int
    starts_at: datetime
    ends_at: datetime
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.starts_at = _require_utc(self.starts_at, "hora de inicio")
        self.ends_at = _require_utc(self.ends_at, "hora de fin")
        if self.ends_at <= self.starts_at:
            raise InvalidSlot("La hora de fin debe ser posterior a la de inicio.")
        if self.duration < MIN_SLOT_DURATION:
            raise InvalidSlot(
                f"Un tramo debe durar al menos {int(MIN_SLOT_DURATION.total_seconds() // 60)} "
                "minutos."
            )
        if self.duration > MAX_SLOT_DURATION:
            raise InvalidSlot(
                f"Un tramo no puede superar las {int(MAX_SLOT_DURATION.total_seconds() // 3600)} "
                "horas. Publicá varios tramos en su lugar."
            )

    @property
    def duration(self) -> timedelta:
        return self.ends_at - self.starts_at

    def overlaps(self, other: AvailabilitySlot) -> bool:
        """Dos tramos se tocan si uno empieza antes de que el otro termine.

        Compartir el extremo no es superponerse: un tramo que termina a las 12
        y otro que empieza a las 12 son contiguos, no simultáneos.
        """
        return self.starts_at < other.ends_at and other.starts_at < self.ends_at

    def covers(self, starts_at: datetime, ends_at: datetime) -> bool:
        """La ventana pedida cabe entera dentro del tramo."""
        return self.starts_at <= starts_at and ends_at <= self.ends_at

    def belongs_to(self, veterinarian_id: int) -> bool:
        return self.veterinarian_id == veterinarian_id


def _require_utc(moment: datetime, field_name: str) -> datetime:
    """Exige una fecha con zona y la normaliza a UTC.

    Una marca sin zona es ambigua, y la ambigüedad en una agenda se paga con
    citas a la hora equivocada.
    """
    if moment.tzinfo is None:
        raise InvalidSlot(f"La {field_name} debe traer zona horaria.")
    return moment.astimezone(UTC)
