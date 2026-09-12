"""Pruebas del adaptador que arma el PDF. Sin base ni servidor."""

from __future__ import annotations

from datetime import UTC, datetime

from gestvet.modules.medical_records.adapters.reports.pdf import ReportLabClinicalHistoryReport
from gestvet.modules.medical_records.domain.attachment import Attachment
from gestvet.modules.medical_records.domain.entities import ClinicalEntry, EntryKind
from gestvet.modules.medical_records.ports.pet_directory import PetSummary

RENDERER = ReportLabClinicalHistoryReport()

PET = PetSummary(name="Rocco", species="Perro", breed="Mestizo", owner_name="Ana Quispe")


def _entrada(**overrides: object) -> ClinicalEntry:
    valores: dict[str, object] = {
        "pet_id": 1,
        "veterinarian_id": 2,
        "kind": EntryKind.CONSULTATION,
        "notes": "Buen estado general.",
        "occurred_at": datetime(2026, 9, 14, 10, 0, tzinfo=UTC),
        "id": 1,
    }
    valores.update(overrides)
    return ClinicalEntry(**valores)  # type: ignore[arg-type]


def test_un_reporte_sin_entradas_igual_produce_un_pdf() -> None:
    pdf = RENDERER.render(PET, [], {})

    assert pdf.startswith(b"%PDF")


def test_un_reporte_con_entradas_y_adjuntos_produce_un_pdf() -> None:
    entrada = _entrada()
    adjunto = Attachment(
        clinical_entry_id=1,
        filename="radiografia.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
        storage_key="clinical-entries/1/a.jpg",
        uploaded_by=2,
        url="http://test/attachments/clinical-entries/1/a.jpg",
    )

    pdf = RENDERER.render(PET, [entrada], {1: [adjunto]})

    assert pdf.startswith(b"%PDF")


def test_los_caracteres_especiales_en_texto_libre_no_rompen_el_pdf() -> None:
    """Notas y diagnóstico son texto libre: pueden traer <, > o & sin avisar."""
    entrada = _entrada(
        notes="Peso < 5kg & apetito normal, sin síntomas > los esperados.",
        diagnosis="R/O <parásitos>",
    )

    pdf = RENDERER.render(PET, [entrada], {})

    assert pdf.startswith(b"%PDF")
