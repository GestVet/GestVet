"""Adaptador que arma el PDF de la historia clínica con ReportLab.

Vive en `adapters/` y no en `core/` porque, a diferencia del envío de correo
o el almacenamiento de adjuntos, sí conoce la forma de una entrada clínica:
no es infraestructura genérica, es la presentación de un dato de este módulo.

Se eligió ReportLab (Python puro) y no una conversión HTML→PDF porque esta
última exige librerías del sistema (Pango, Cairo) que complican tanto el
desarrollo en Windows como, más adelante, el despliegue, sin que todavía esté
decidido dónde va a correr el backend.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from gestvet.modules.medical_records.domain.attachment import Attachment
from gestvet.modules.medical_records.domain.entities import ClinicalEntry
from gestvet.modules.medical_records.ports.pet_directory import PetSummary

# Trujillo, Perú, igual que la ventana horaria de citas: el reporte lo lee la
# clínica y su dueño, no tiene sentido mostrarles la hora en UTC.
_CLINIC_UTC_OFFSET = timedelta(hours=-5)
_FORMATO_FECHA = "%d/%m/%Y %H:%M"


class ReportLabClinicalHistoryReport:
    def render(
        self,
        pet: PetSummary,
        entries: list[ClinicalEntry],
        attachments_by_entry: dict[int, list[Attachment]],
    ) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=f"Historia clínica de {pet.name}",
        )

        styles = getSampleStyleSheet()
        story = [
            Paragraph("GestVet", styles["Title"]),
            Paragraph("Historia clínica", styles["Heading2"]),
            Spacer(1, 0.3 * cm),
            self._pet_table(pet),
            Spacer(1, 0.6 * cm),
        ]

        if not entries:
            story.append(
                Paragraph("Todavía no hay entradas en la historia clínica.", styles["BodyText"])
            )
        for entry in entries:
            story.extend(self._entry_block(entry, attachments_by_entry.get(entry.id or 0, [])))

        document.build(story)
        return buffer.getvalue()

    def _pet_table(self, pet: PetSummary) -> Table:
        especie = f"{pet.species} / {pet.breed}" if pet.breed else pet.species
        peso = f"{pet.weight_kg} kg" if pet.weight_kg is not None else "—"
        altura = f"{pet.height_cm} cm" if pet.height_cm is not None else "—"
        esterilizado = _si_no_o_desconocido(pet.is_sterilized)
        filas = [
            ["Mascota", escape(pet.name)],
            ["Especie / raza", escape(especie)],
            ["Dueño", escape(pet.owner_name)],
            ["Sexo", escape(pet.sex_label)],
            ["Color", escape(pet.color) or "—"],
            ["Peso / altura", f"{peso} / {altura}"],
            ["Esterilizado", esterilizado],
            ["Microchip", escape(pet.microchip_number) or "—"],
            ["Temperamento", escape(pet.temperament) or "—"],
            ["Alergias", escape(pet.allergies) or "—"],
            ["Emitido", _a_hora_local(datetime.now(UTC))],
        ]
        tabla = Table(filas, colWidths=[4 * cm, 12 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return tabla

    def _entry_block(self, entry: ClinicalEntry, attachments: list[Attachment]) -> list:
        styles = getSampleStyleSheet()
        cuerpo = styles["BodyText"]
        fecha = _a_hora_local(entry.occurred_at)
        encabezado = Paragraph(f"<b>{fecha} — {escape(entry.kind.label)}</b>", styles["Heading4"])

        nombres = (
            ", ".join(escape(adjunto.filename) for adjunto in attachments)
            if attachments
            else "Sin adjuntos"
        )
        peso = f"{entry.weight_kg} kg" if entry.weight_kg is not None else "—"
        campos = [
            ("Diagnóstico", escape(entry.diagnosis) or "—"),
            ("Tratamiento", escape(entry.treatment) or "—"),
            ("Peso", peso),
            ("Notas", escape(entry.notes)),
            ("Adjuntos", nombres),
        ]

        filas = [
            [Paragraph(f"<b>{campo}</b>", cuerpo), Paragraph(valor, cuerpo)]
            for campo, valor in campos
        ]
        tabla = Table(filas, colWidths=[3.5 * cm, 12.5 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.lightgrey),
                ]
            )
        )
        return [encabezado, tabla, Spacer(1, 0.4 * cm)]


def _a_hora_local(momento: datetime) -> str:
    return (momento + _CLINIC_UTC_OFFSET).strftime(_FORMATO_FECHA)


def _si_no_o_desconocido(valor: bool | None) -> str:
    if valor is None:
        return "No evaluado"
    return "Sí" if valor else "No"
