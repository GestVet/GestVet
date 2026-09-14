"""Caso de uso: resumir con IA la historia de una mascota antes de la consulta.

Al modelo le llega la ficha, el carnet de vacunas y la historia clínica de la
mascota. No le llega nada de la persona dueña (nombre, DNI, teléfono): no hace
falta para resumir y así ningún dato personal sale del sistema.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from gestvet.core.llm import JsonCompletionRequest, LlmClient
from gestvet.modules.medical_records.domain.clinical_summary import (
    SUMMARY_SCHEMA,
    ClinicalSummary,
    summary_from_response,
)
from gestvet.modules.medical_records.domain.entities import ClinicalEntry
from gestvet.modules.medical_records.domain.exceptions import PetNotFound
from gestvet.modules.medical_records.domain.vaccination import VaccineStatusSummary, summarize
from gestvet.modules.medical_records.ports.clinical_entry_repository import ClinicalEntryRepository
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory, PetSummary
from gestvet.modules.medical_records.ports.vaccination_repository import VaccinationRepository

# Las últimas entradas alcanzan para preparar una consulta y acotan el costo.
MAX_ENTRIES = 30
MAX_NOTE_CHARS = 600
MAX_OUTPUT_TOKENS = 900

SYSTEM_PROMPT = """Eres un asistente para médicos veterinarios de una clínica en Perú.
Recibes la ficha, el carnet de vacunas y la historia clínica de una sola mascota.
Tu tarea es preparar al veterinario antes de la consulta, en español y con tuteo:
- "resumen": de 3 a 5 oraciones con lo más relevante: problemas que se repiten,
  tratamientos, evolución del peso y estado de las vacunas.
- "alertas": lo que no debe pasarse por alto: alergias, vacunas vencidas o por
  vencer, cambios bruscos de peso, datos importantes que faltan en la ficha.
- "pendientes": controles, refuerzos o seguimientos que corresponden según los datos.
Reglas:
- Usa solo los datos recibidos. No inventes ni supongas lo que no está escrito.
- No propongas diagnósticos nuevos ni dosis de medicamentos.
- Si hay pocos datos, dilo en el resumen y deja las listas vacías si no aplica."""


def _decimal(value: Decimal | None, unit: str) -> str:
    return "sin dato" if value is None else f"{value} {unit}"


def _pet_lines(pet: PetSummary, today: date) -> list[str]:
    sterilized = {True: "sí", False: "no", None: "no evaluado"}[pet.is_sterilized]
    birth = "sin dato" if pet.birth_date is None else pet.birth_date.isoformat()
    return [
        f"Fecha de hoy: {today.isoformat()}",
        f"Mascota: {pet.name}. Especie: {pet.species}. Raza: {pet.breed}. Sexo: {pet.sex_label}.",
        f"Nacimiento: {birth}. Peso: {_decimal(pet.weight_kg, 'kg')}. "
        f"Altura: {_decimal(pet.height_cm, 'cm')}. Esterilizada: {sterilized}.",
        f"Alergias o condiciones crónicas: {pet.allergies or 'ninguna registrada'}.",
        f"Temperamento: {pet.temperament or 'sin dato'}.",
    ]


def _vaccine_lines(card: list[VaccineStatusSummary]) -> list[str]:
    if not card:
        return ["Carnet de vacunas: sin vacunas registradas."]
    lines = ["Carnet de vacunas (última dosis de cada una):"]
    for item in card:
        next_due = item.next_due_on.isoformat() if item.next_due_on else "sin refuerzo"
        lines.append(
            f"- {item.label}: aplicada {item.last_applied_on.isoformat()}, "
            f"próxima {next_due}, estado {item.status.label}."
        )
    return lines


def _entry_lines(entries: list[ClinicalEntry]) -> list[str]:
    if not entries:
        return ["Historia clínica: sin entradas."]
    lines = [f"Historia clínica (de la más antigua a la más reciente, hasta {MAX_ENTRIES}):"]
    for entry in entries:
        parts = [entry.occurred_at.date().isoformat(), entry.kind.label]
        if entry.diagnosis:
            parts.append(f"diagnóstico: {entry.diagnosis}")
        if entry.treatment:
            parts.append(f"tratamiento: {entry.treatment}")
        if entry.weight_kg is not None:
            parts.append(f"peso: {entry.weight_kg} kg")
        parts.append(f"notas: {entry.notes[:MAX_NOTE_CHARS]}")
        lines.append("- " + " · ".join(parts))
    return lines


def build_context(
    pet: PetSummary,
    entries: list[ClinicalEntry],
    card: list[VaccineStatusSummary],
    today: date,
) -> str:
    """El texto que recibe el modelo. Nunca incluye datos de la persona dueña."""
    return "\n".join(
        [*_pet_lines(pet, today), "", *_vaccine_lines(card), "", *_entry_lines(entries)]
    )


class SummarizeClinicalHistory:
    def __init__(
        self,
        entries: ClinicalEntryRepository,
        vaccinations: VaccinationRepository,
        pets: PetDirectory,
        llm: LlmClient,
    ) -> None:
        self._entries = entries
        self._vaccinations = vaccinations
        self._pets = pets
        self._llm = llm

    async def __call__(self, pet_id: int, today: date) -> ClinicalSummary:
        pet = await self._pets.summary(pet_id)
        if pet is None:
            raise PetNotFound(pet_id)
        entries = (await self._entries.list_all_for_pet(pet_id))[-MAX_ENTRIES:]
        card = summarize(await self._vaccinations.list_for_pet(pet_id), today)

        completion = await self._llm.complete_json(
            JsonCompletionRequest(
                system=SYSTEM_PROMPT,
                user=build_context(pet, entries, card, today),
                schema_name="resumen_clinico",
                schema=SUMMARY_SCHEMA,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            )
        )
        return summary_from_response(completion.data, completion.model)
