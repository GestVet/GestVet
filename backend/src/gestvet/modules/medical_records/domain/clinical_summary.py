"""Resumen de la historia clínica hecho por el asistente de IA.

Lo que devuelve un modelo se trata como un dato de afuera: se valida la forma,
se recortan los largos y se descarta lo que no sea texto. El resumen orienta al
veterinario; no reemplaza leer la historia ni decide nada.

Python puro.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gestvet.core.llm import LlmUnavailable

MAX_SUMMARY_LENGTH = 1200
MAX_ITEMS = 6
MAX_ITEM_LENGTH = 240

# La forma que se le pide al modelo. Las claves van en español porque el modelo
# escribe mejor cuando el pedido y el formato están en el mismo idioma.
SUMMARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "resumen": {"type": "string"},
        "alertas": {"type": "array", "items": {"type": "string"}},
        "pendientes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["resumen", "alertas", "pendientes"],
    "additionalProperties": False,
}


@dataclass(frozen=True, slots=True)
class ClinicalSummary:
    summary: str
    alerts: tuple[str, ...]
    follow_ups: tuple[str, ...]
    model: str


def _items(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    texts = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return tuple(text[:MAX_ITEM_LENGTH] for text in texts[:MAX_ITEMS])


def summary_from_response(data: dict[str, Any], model: str) -> ClinicalSummary:
    summary = data.get("resumen")
    if not isinstance(summary, str) or not summary.strip():
        raise LlmUnavailable("El asistente no devolvió un resumen. Inténtalo de nuevo.")
    return ClinicalSummary(
        summary=summary.strip()[:MAX_SUMMARY_LENGTH],
        alerts=_items(data.get("alertas")),
        follow_ups=_items(data.get("pendientes")),
        model=model,
    )
