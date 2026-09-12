"""Entidad de dominio: adjunto de una entrada clínica.

Un archivo (radiografía, análisis) nunca se guarda en la base de datos: acá
solo vive la referencia. El archivo en sí lo guarda `AttachmentStorage`, un
puerto aparte, para que el dominio nunca sepa dónde termina guardado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from gestvet.modules.medical_records.domain.exceptions import InvalidAttachment

MAX_FILENAME_LENGTH = 150

# 10 MB alcanza para una radiografía escaneada o un PDF de análisis, sin abrir
# la puerta a subir cualquier cosa.
MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    }
)


@dataclass(slots=True)
class Attachment:
    clinical_entry_id: int
    filename: str
    content_type: str
    size_bytes: int
    storage_key: str
    uploaded_by: int
    # Se completa después de guardar el archivo en el almacenamiento: no es
    # un dato del usuario y no tiene regla de negocio que validar.
    url: str = ""
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.filename = self.filename.strip()
        if not self.filename:
            raise InvalidAttachment("El archivo necesita un nombre.")
        if len(self.filename) > MAX_FILENAME_LENGTH:
            raise InvalidAttachment(
                f"El nombre del archivo admite {MAX_FILENAME_LENGTH} caracteres como máximo."
            )
        if self.content_type not in ALLOWED_CONTENT_TYPES:
            raise InvalidAttachment("Solo se aceptan imágenes (JPEG, PNG, WEBP) o PDF.")
        if self.size_bytes <= 0:
            raise InvalidAttachment("El archivo está vacío.")
        if self.size_bytes > MAX_ATTACHMENT_SIZE_BYTES:
            max_mb = MAX_ATTACHMENT_SIZE_BYTES // (1024 * 1024)
            raise InvalidAttachment(f"El archivo supera los {max_mb} MB permitidos.")
