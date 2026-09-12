"""Pruebas del dominio de internaciones. Python puro, sin base ni servidor."""

from __future__ import annotations

import pytest

from gestvet.modules.hospitalizations.domain.entities import (
    Hospitalization,
    HospitalizationNote,
    HospitalizationStatus,
)
from gestvet.modules.hospitalizations.domain.exceptions import (
    HospitalizationAlreadyDischarged,
    InvalidHospitalization,
)


def _internacion(**overrides: object) -> Hospitalization:
    valores: dict[str, object] = {
        "appointment_id": 1,
        "pet_id": 2,
        "opened_by": 3,
        "reason": "Cirugía de emergencia, queda en observación.",
    }
    valores.update(overrides)
    return Hospitalization(**valores)  # type: ignore[arg-type]


def test_el_motivo_es_obligatorio() -> None:
    with pytest.raises(InvalidHospitalization):
        _internacion(reason="   ")


def test_el_motivo_no_puede_exceder_su_largo() -> None:
    with pytest.raises(InvalidHospitalization):
        _internacion(reason="x" * 301)


def test_nace_abierta() -> None:
    internacion = _internacion()

    assert internacion.status is HospitalizationStatus.OPEN
    assert internacion.is_open


def test_dar_de_alta_cierra_la_internacion() -> None:
    internacion = _internacion()

    internacion.discharge("Se recuperó bien, vuelve a casa.")

    assert internacion.status is HospitalizationStatus.DISCHARGED
    assert not internacion.is_open
    assert internacion.discharge_notes == "Se recuperó bien, vuelve a casa."
    assert internacion.discharged_at is not None


def test_no_se_puede_dar_de_alta_dos_veces() -> None:
    internacion = _internacion()
    internacion.discharge("Vuelve a casa.")

    with pytest.raises(HospitalizationAlreadyDischarged):
        internacion.discharge("De nuevo.")


def test_las_notas_de_alta_respetan_su_largo_maximo() -> None:
    internacion = _internacion()

    with pytest.raises(InvalidHospitalization):
        internacion.discharge("x" * 1001)


def _nota(**overrides: object) -> HospitalizationNote:
    valores: dict[str, object] = {
        "hospitalization_id": 1,
        "author_id": 2,
        "note": "Comió bien, signos vitales estables.",
    }
    valores.update(overrides)
    return HospitalizationNote(**valores)  # type: ignore[arg-type]


def test_la_nota_es_obligatoria() -> None:
    with pytest.raises(InvalidHospitalization):
        _nota(note="   ")


def test_la_nota_no_puede_exceder_su_largo() -> None:
    with pytest.raises(InvalidHospitalization):
        _nota(note="x" * 1001)
