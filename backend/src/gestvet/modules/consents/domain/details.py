"""Lo que el veterinario agrega a un consentimiento que pide.

La plantilla dice lo general ("autorizo la cirugía"); el detalle dice cuál,
con qué pronóstico y a qué costo aproximado. Va copiado debajo del texto de la
plantilla, así que lo que el dueño firma es exactamente lo que leyó, detalle
incluido.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from gestvet.modules.consents.domain.exceptions import InvalidConsentDetails

MAX_PROCEDURE_LENGTH = 200
MAX_PROGNOSIS_LENGTH = 500
MAX_NOTES_LENGTH = 1000
MAX_ESTIMATED_COST = Decimal("1000000")
_CENTIMOS = Decimal("0.01")

DETAILS_HEADING = "Detalle indicado por el médico veterinario:"


def _trimmed(raw: str | None, label: str, max_length: int) -> str:
    cleaned = " ".join((raw or "").split())
    if len(cleaned) > max_length:
        raise InvalidConsentDetails(f"{label} admite {max_length} caracteres como máximo.")
    return cleaned


def _trimmed_block(raw: str | None, label: str, max_length: int) -> str:
    # Las observaciones pueden traer párrafos: se conservan los saltos de
    # línea y se recortan los espacios de cada línea.
    lines = [" ".join(line.split()) for line in (raw or "").strip().splitlines()]
    cleaned = "\n".join(lines).strip()
    if len(cleaned) > max_length:
        raise InvalidConsentDetails(f"{label} admite {max_length} caracteres como máximo.")
    return cleaned


def _cost(raw: Decimal | str | None) -> Decimal | None:
    if raw is None or raw == "":
        return None
    try:
        value = Decimal(str(raw))
    except InvalidOperation as error:
        raise InvalidConsentDetails("El costo estimado tiene que ser un monto.") from error
    if not value.is_finite() or value <= 0:
        raise InvalidConsentDetails("El costo estimado tiene que ser mayor que cero.")
    if value > MAX_ESTIMATED_COST:
        raise InvalidConsentDetails("El costo estimado es demasiado alto; revisá el monto.")
    return value.quantize(_CENTIMOS, rounding=ROUND_HALF_UP)


def format_soles(amount: Decimal) -> str:
    """Un monto en soles tal como se lee en el Perú: `S/ 1,250.00`."""
    return f"S/ {amount:,.2f}"


@dataclass(frozen=True, slots=True)
class ConsentDetails:
    procedure: str = ""
    prognosis: str = ""
    estimated_cost: Decimal | None = None
    notes: str = ""

    @classmethod
    def build(
        cls,
        *,
        procedure: str | None = None,
        prognosis: str | None = None,
        estimated_cost: Decimal | str | None = None,
        notes: str | None = None,
        procedure_required: bool = False,
    ) -> ConsentDetails:
        details = cls(
            procedure=_trimmed(procedure, "El procedimiento", MAX_PROCEDURE_LENGTH),
            prognosis=_trimmed_block(prognosis, "El pronóstico", MAX_PROGNOSIS_LENGTH),
            estimated_cost=_cost(estimated_cost),
            notes=_trimmed_block(notes, "Las observaciones", MAX_NOTES_LENGTH),
        )
        if procedure_required and not details.procedure:
            raise InvalidConsentDetails(
                "Indicá el procedimiento: el responsable tiene que saber qué autoriza."
            )
        return details

    @property
    def is_empty(self) -> bool:
        return not (self.procedure or self.prognosis or self.notes) and self.estimated_cost is None

    def lines(self) -> list[str]:
        lines: list[str] = []
        if self.procedure:
            lines.append(f"- Procedimiento: {self.procedure}")
        if self.prognosis:
            lines.append(f"- Pronóstico: {self.prognosis}")
        if self.estimated_cost is not None:
            lines.append(
                f"- Costo estimado: {format_soles(self.estimated_cost)} "
                "(aproximado; el costo final depende de la evolución)"
            )
        if self.notes:
            lines.append(f"- Observaciones: {self.notes}")
        return lines

    def render_below(self, text: str) -> str:
        """El texto de la plantilla con el detalle debajo, si hay detalle."""
        if self.is_empty:
            return text
        return "\n".join([text, "", DETAILS_HEADING, *self.lines()])

    def to_json(self) -> dict[str, object] | None:
        """Solo lo que se completó. El costo va como texto para no perder centavos."""
        data: dict[str, object] = {}
        if self.procedure:
            data["procedure"] = self.procedure
        if self.prognosis:
            data["prognosis"] = self.prognosis
        if self.estimated_cost is not None:
            data["estimated_cost"] = str(self.estimated_cost)
        if self.notes:
            data["notes"] = self.notes
        return data or None

    @classmethod
    def from_json(cls, data: dict[str, object] | None) -> ConsentDetails:
        if not data:
            return cls()
        cost = data.get("estimated_cost")
        return cls(
            procedure=str(data.get("procedure") or ""),
            prognosis=str(data.get("prognosis") or ""),
            estimated_cost=Decimal(str(cost)) if cost not in (None, "") else None,
            notes=str(data.get("notes") or ""),
        )
