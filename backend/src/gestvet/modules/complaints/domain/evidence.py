"""Entidad de dominio: evidencia adjunta a un reclamo.

El archivo en sí lo guarda `EvidenceStorage`, un puerto aparte: acá solo vive
la referencia (nombre, tipo, tamaño, clave), igual que hace `Attachment` en
`medical_records`. No se comparte código entre los dos módulos -son
independientes-, pero sí el criterio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from gestvet.modules.complaints.domain.exceptions import InvalidEvidence

MAX_FILENAME_LENGTH = 150
MAX_EVIDENCE_SIZE_BYTES = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    }
)


@dataclass(slots=True)
class ComplaintEvidence:
    complaint_id: int
    filename: str
    content_type: str
    size_bytes: int
    storage_key: str
    uploaded_by: int
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.filename = self.filename.strip()
        if not self.filename:
            raise InvalidEvidence("El archivo necesita un nombre.")
        if len(self.filename) > MAX_FILENAME_LENGTH:
            raise InvalidEvidence(
                f"El nombre del archivo admite {MAX_FILENAME_LENGTH} caracteres como máximo."
            )
        if self.content_type not in ALLOWED_CONTENT_TYPES:
            raise InvalidEvidence("Solo se aceptan imágenes (JPEG, PNG, WEBP) o PDF.")
        if self.size_bytes <= 0:
            raise InvalidEvidence("El archivo está vacío.")
        if self.size_bytes > MAX_EVIDENCE_SIZE_BYTES:
            max_mb = MAX_EVIDENCE_SIZE_BYTES // (1024 * 1024)
            raise InvalidEvidence(f"El archivo supera los {max_mb} MB permitidos.")
