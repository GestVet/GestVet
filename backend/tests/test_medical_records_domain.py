"""Pruebas del dominio de la historia clínica. Python puro, sin base ni servidor."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from gestvet.modules.medical_records.domain.entities import ClinicalEntry, EntryKind
from gestvet.modules.medical_records.domain.exceptions import InvalidClinicalEntry

BASE = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)


def _entrada(**overrides: object) -> ClinicalEntry:
    valores: dict[str, object] = {
        "pet_id": 1,
        "veterinarian_id": 2,
        "kind": EntryKind.CONSULTATION,
        "notes": "Se observa buen estado general.",
        "occurred_at": BASE,
    }
    valores.update(overrides)
    return ClinicalEntry(**valores)  # type: ignore[arg-type]


def test_la_fecha_debe_traer_zona_horaria() -> None:
    with pytest.raises(InvalidClinicalEntry):
        _entrada(occurred_at=BASE.replace(tzinfo=None))


def test_las_notas_son_obligatorias() -> None:
    with pytest.raises(InvalidClinicalEntry):
        _entrada(notes="   ")


def test_las_notas_no_pueden_exceder_su_largo() -> None:
    with pytest.raises(InvalidClinicalEntry):
        _entrada(notes="x" * 2001)


def test_el_diagnostico_y_el_tratamiento_son_opcionales() -> None:
    entrada = _entrada()

    assert entrada.diagnosis == ""
    assert entrada.treatment == ""


def test_el_diagnostico_no_puede_exceder_su_largo() -> None:
    with pytest.raises(InvalidClinicalEntry):
        _entrada(diagnosis="x" * 301)


@pytest.mark.parametrize("peso", [Decimal("0"), Decimal("-1"), Decimal("150")])
def test_el_peso_debe_ser_plausible(peso: Decimal) -> None:
    with pytest.raises(InvalidClinicalEntry):
        _entrada(weight_kg=peso)


def test_un_peso_plausible_se_acepta() -> None:
    entrada = _entrada(weight_kg=Decimal("12.5"))

    assert entrada.weight_kg == Decimal("12.5")


def test_cada_tipo_de_entrada_tiene_etiqueta() -> None:
    assert EntryKind.VACCINE.label == "Vacuna"
    assert EntryKind.SURGERY.label == "Cirugía"
