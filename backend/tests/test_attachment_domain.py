"""Pruebas del dominio del adjunto. Python puro, sin base ni servidor."""

from __future__ import annotations

import pytest

from gestvet.modules.medical_records.domain.attachment import (
    MAX_ATTACHMENT_SIZE_BYTES,
    MAX_FILENAME_LENGTH,
    Attachment,
)
from gestvet.modules.medical_records.domain.exceptions import InvalidAttachment


def _adjunto(**overrides: object) -> Attachment:
    valores: dict[str, object] = {
        "clinical_entry_id": 1,
        "filename": "radiografia.jpg",
        "content_type": "image/jpeg",
        "size_bytes": 1024,
        "storage_key": "clinical-entries/1/abc123.jpg",
        "uploaded_by": 2,
    }
    valores.update(overrides)
    return Attachment(**valores)  # type: ignore[arg-type]


def test_el_nombre_es_obligatorio() -> None:
    with pytest.raises(InvalidAttachment):
        _adjunto(filename="   ")


def test_el_nombre_no_puede_exceder_su_largo() -> None:
    with pytest.raises(InvalidAttachment):
        _adjunto(filename="x" * (MAX_FILENAME_LENGTH + 1))


def test_solo_se_aceptan_los_tipos_permitidos() -> None:
    with pytest.raises(InvalidAttachment):
        _adjunto(content_type="application/zip")


@pytest.mark.parametrize("tipo", ["image/jpeg", "image/png", "image/webp", "application/pdf"])
def test_los_tipos_permitidos_se_aceptan(tipo: str) -> None:
    adjunto = _adjunto(content_type=tipo)

    assert adjunto.content_type == tipo


def test_el_archivo_no_puede_estar_vacio() -> None:
    with pytest.raises(InvalidAttachment):
        _adjunto(size_bytes=0)


def test_el_archivo_no_puede_superar_el_tamano_maximo() -> None:
    with pytest.raises(InvalidAttachment):
        _adjunto(size_bytes=MAX_ATTACHMENT_SIZE_BYTES + 1)


def test_el_tamano_maximo_se_acepta() -> None:
    adjunto = _adjunto(size_bytes=MAX_ATTACHMENT_SIZE_BYTES)

    assert adjunto.size_bytes == MAX_ATTACHMENT_SIZE_BYTES
