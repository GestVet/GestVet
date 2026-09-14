"""Puerto de persistencia del carnet de vacunas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from gestvet.modules.medical_records.domain.vaccination import Vaccination


class VaccinationRepository(Protocol):
    async def add(self, vaccination: Vaccination) -> Vaccination: ...

    async def list_for_pet(self, pet_id: int) -> list[Vaccination]:
        """Todas las vacunas de una mascota, la más reciente primero."""
        ...

    async def find_due_for_reminder(self, first_day: date, last_day: date) -> list[Vaccination]:
        """Las dosis que vencen entre esos dos días, sin aviso y sin un refuerzo posterior."""
        ...

    async def mark_reminder_sent(self, vaccination_id: int, sent_at: datetime) -> None: ...
