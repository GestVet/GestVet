"""Puerto del carnet de vacunas en PDF.

El caso de uso junta los datos y el enlace de verificación; el adaptador los
dibuja. Así el negocio no sabe con qué librería se arma el PDF ni el QR.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from gestvet.modules.medical_records.domain.vaccination import Vaccination, VaccineStatusSummary
from gestvet.modules.medical_records.ports.pet_directory import PetSummary


@dataclass(frozen=True, slots=True)
class VaccinationCardDocument:
    pet: PetSummary
    summary: list[VaccineStatusSummary]
    items: list[Vaccination]
    verification_url: str
    issued_on: date
    valid_until: date


class VaccinationCardRenderer(Protocol):
    def render(self, card: VaccinationCardDocument) -> bytes: ...
