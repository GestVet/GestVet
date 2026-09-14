"""Adaptador que dibuja el carnet de vacunas en PDF con ReportLab.

Una página A4 que se puede imprimir o mandar por WhatsApp: arriba los datos de
la mascota y el código QR para verificarlo, después el estado de cada vacuna y
todas las aplicaciones con producto y lote.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from gestvet.core.qrcode_image import render_qr_png
from gestvet.modules.medical_records.domain.vaccination import VaccinationStatus
from gestvet.modules.medical_records.ports.vaccination_card_report import VaccinationCardDocument

_QR_SIZE = 3.8 * cm
_HEADER_FILL = colors.HexColor("#E8EEF6")
_STATUS_COLORS = {
    VaccinationStatus.OVERDUE: colors.HexColor("#B42318"),
    VaccinationStatus.DUE_SOON: colors.HexColor("#9A6700"),
    VaccinationStatus.UP_TO_DATE: colors.HexColor("#1A7F37"),
    VaccinationStatus.NO_BOOSTER: colors.HexColor("#555555"),
}


def _day(value: date | None) -> str:
    return "—" if value is None else value.strftime("%d/%m/%Y")


def _grid(rows: list[list[object]], widths: list[float]) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_FILL),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


class ReportLabVaccinationCard:
    def render(self, card: VaccinationCardDocument) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=1.8 * cm,
            rightMargin=1.8 * cm,
            topMargin=1.6 * cm,
            bottomMargin=1.6 * cm,
            title=f"Carnet de vacunas de {card.pet.name}",
        )
        styles = getSampleStyleSheet()
        story: list[object] = [
            Paragraph("GestVet · Carnet de vacunas", styles["Title"]),
            self._header(card),
            Spacer(1, 0.5 * cm),
            Paragraph("Estado de las vacunas", styles["Heading3"]),
            self._status(card),
            Spacer(1, 0.5 * cm),
            Paragraph("Aplicaciones", styles["Heading3"]),
            self._history(card),
            Spacer(1, 0.6 * cm),
            Paragraph(self._footer(card), styles["Italic"]),
        ]
        document.build(story)
        return buffer.getvalue()

    def _header(self, card: VaccinationCardDocument) -> Table:
        pet = card.pet
        breed = f"{pet.species} / {pet.breed}" if pet.breed else pet.species
        rows = [
            ["Mascota", escape(pet.name)],
            ["Especie / raza", escape(breed)],
            ["Sexo", escape(pet.sex_label)],
            ["Nacimiento", _day(pet.birth_date)],
            ["Color", escape(pet.color) or "—"],
            ["Microchip", escape(pet.microchip_number) or "Sin microchip"],
            ["Dueño", escape(pet.owner_name)],
            ["Emitido", _day(card.issued_on)],
        ]
        details = Table(rows, colWidths=[3.2 * cm, 8.8 * cm])
        details.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        qr = Image(BytesIO(render_qr_png(card.verification_url)), width=_QR_SIZE, height=_QR_SIZE)
        caption = Paragraph(
            "<font size=8>Escanéalo para verificar el carnet</font>",
            getSampleStyleSheet()["BodyText"],
        )
        layout = Table([[details, [qr, caption]]], colWidths=[12.2 * cm, 5.2 * cm])
        layout.setStyle(
            TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "CENTER")])
        )
        return layout

    def _status(self, card: VaccinationCardDocument) -> Table | Paragraph:
        body = getSampleStyleSheet()["BodyText"]
        if not card.summary:
            return Paragraph("Todavía no hay vacunas registradas.", body)
        rows: list[list[object]] = [["Vacuna", "Última dosis", "Próxima dosis", "Estado"]]
        for item in card.summary:
            color = _STATUS_COLORS[item.status].hexval()
            rows.append(
                [
                    Paragraph(escape(item.label), body),
                    _day(item.last_applied_on),
                    _day(item.next_due_on),
                    Paragraph(f'<font color="{color}"><b>{item.status.label}</b></font>', body),
                ]
            )
        return _grid(rows, [7.2 * cm, 3.2 * cm, 3.4 * cm, 3.6 * cm])

    def _history(self, card: VaccinationCardDocument) -> Table | Paragraph:
        body = getSampleStyleSheet()["BodyText"]
        if not card.items:
            return Paragraph("Todavía no hay vacunas registradas.", body)
        rows: list[list[object]] = [["Aplicada", "Vacuna", "Producto", "Lote", "Próxima"]]
        rows.extend(
            [
                _day(item.applied_on),
                Paragraph(escape(item.label), body),
                Paragraph(escape(item.product_name) or "—", body),
                escape(item.batch) or "—",
                _day(item.next_due_on),
            ]
            for item in card.items
        )
        return _grid(rows, [2.6 * cm, 5.6 * cm, 4.2 * cm, 2.6 * cm, 2.4 * cm])

    def _footer(self, card: VaccinationCardDocument) -> str:
        return (
            f"Refleja lo registrado en la clínica al {_day(card.issued_on)}. "
            "El código QR muestra el estado actualizado de las vacunas, sin datos del dueño, "
            f"hasta el {_day(card.valid_until)}."
        )
