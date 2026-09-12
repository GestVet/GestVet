"""Puerto de generación del reporte en PDF.

El caso de uso arma los datos y le pide al adaptador que los convierta en
bytes: así el negocio no sabe con qué librería se dibuja el PDF. Separado del
puerto de almacenamiento de adjuntos porque acá no se guarda nada, se genera
al vuelo en cada pedido.
"""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.medical_records.domain.attachment import Attachment
from gestvet.modules.medical_records.domain.entities import ClinicalEntry
from gestvet.modules.medical_records.ports.pet_directory import PetSummary


class ClinicalHistoryReportRenderer(Protocol):
    def render(
        self,
        pet: PetSummary,
        entries: list[ClinicalEntry],
        attachments_by_entry: dict[int, list[Attachment]],
    ) -> bytes: ...
