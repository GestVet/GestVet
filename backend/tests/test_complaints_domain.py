"""Pruebas del dominio de reclamos. Python puro, sin base ni servidor."""

from __future__ import annotations

import pytest

from gestvet.modules.complaints.domain.entities import Complaint
from gestvet.modules.complaints.domain.evidence import ComplaintEvidence
from gestvet.modules.complaints.domain.exceptions import InvalidComplaint, InvalidEvidence


def _reclamo(**overrides: object) -> Complaint:
    valores: dict[str, object] = {
        "client_id": 1,
        "veterinarian_id": 2,
        "appointment_id": 3,
        "description": "El veterinario no revisó bien a mi mascota.",
    }
    valores.update(overrides)
    return Complaint(**valores)  # type: ignore[arg-type]


def test_la_descripcion_es_obligatoria() -> None:
    with pytest.raises(InvalidComplaint):
        _reclamo(description="   ")


def test_la_descripcion_no_puede_exceder_su_largo() -> None:
    with pytest.raises(InvalidComplaint):
        _reclamo(description="x" * 2001)


def _evidencia(**overrides: object) -> ComplaintEvidence:
    valores: dict[str, object] = {
        "complaint_id": 1,
        "filename": "foto.jpg",
        "content_type": "image/jpeg",
        "size_bytes": 1024,
        "storage_key": "complaints/1/a.jpg",
        "uploaded_by": 2,
    }
    valores.update(overrides)
    return ComplaintEvidence(**valores)  # type: ignore[arg-type]


def test_solo_se_aceptan_los_tipos_permitidos() -> None:
    with pytest.raises(InvalidEvidence):
        _evidencia(content_type="application/zip")


def test_el_archivo_no_puede_estar_vacio() -> None:
    with pytest.raises(InvalidEvidence):
        _evidencia(size_bytes=0)
