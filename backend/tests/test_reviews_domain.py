"""Pruebas del dominio de reseñas. Python puro, sin base ni servidor."""

from __future__ import annotations

import pytest

from gestvet.modules.reviews.domain.entities import Review
from gestvet.modules.reviews.domain.exceptions import InappropriateComment, InvalidReview


def _resena(**overrides: object) -> Review:
    valores: dict[str, object] = {
        "veterinarian_id": 1,
        "client_id": 2,
        "rating": 5,
        "comment": "Excelente atención, muy atento con mi mascota.",
    }
    valores.update(overrides)
    return Review(**valores)  # type: ignore[arg-type]


@pytest.mark.parametrize("calificacion", [0, 6, -1])
def test_la_calificacion_debe_estar_en_rango(calificacion: int) -> None:
    with pytest.raises(InvalidReview):
        _resena(rating=calificacion)


def test_el_comentario_es_obligatorio() -> None:
    with pytest.raises(InvalidReview):
        _resena(comment="   ")


def test_el_comentario_no_puede_exceder_su_largo() -> None:
    with pytest.raises(InvalidReview):
        _resena(comment="x" * 501)


def test_el_comentario_no_admite_groserias() -> None:
    with pytest.raises(InappropriateComment):
        _resena(comment="Que veterinario tan pendejo, no vuelvo mas")


def test_actualizar_cambia_la_calificacion_y_el_comentario() -> None:
    resena = _resena(rating=2, comment="No me gustó la atención")

    resena.update(rating=5, comment="Corrijo: en realidad estuvo muy bien")

    assert resena.rating == 5
    assert resena.comment == "Corrijo: en realidad estuvo muy bien"


def test_actualizar_tambien_valida() -> None:
    resena = _resena()

    with pytest.raises(InvalidReview):
        resena.update(rating=10, comment="Bien")
