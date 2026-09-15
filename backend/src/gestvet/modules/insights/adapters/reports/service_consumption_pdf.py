"""Adaptador que dibuja el reporte de servicios más consumidos en PDF con ReportLab."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from gestvet.modules.insights.ports.service_consumption_report import ServiceConsumptionDocument

_HEADER_FILL = colors.HexColor("#E8EEF6")


def _day(value: date | None) -> str:
    return "—" if value is None else value.strftime("%d/%m/%Y")


class ReportLabServiceConsumptionReport:
    def render(self, document: ServiceConsumptionDocument) -> bytes:
        buffer = BytesIO()
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=1.8 * cm,
            rightMargin=1.8 * cm,
            topMargin=1.6 * cm,
            bottomMargin=1.6 * cm,
            title="Servicios más consumidos",
        )
        styles = getSampleStyleSheet()
        story: list[object] = [
            Paragraph("GestVet · Servicios más consumidos", styles["Title"]),
            Paragraph(self._subtitle(document), styles["BodyText"]),
            Spacer(1, 0.5 * cm),
            self._table(document, styles),
            Spacer(1, 0.5 * cm),
            Paragraph(
                f"Generado el {_day(document.generated_at)}. "
                "El ingreso es estimado con el precio de catálogo de cada servicio, "
                "no con los pagos reales.",
                styles["Italic"],
            ),
        ]
        pdf.build(story)
        return buffer.getvalue()

    def _subtitle(self, document: ServiceConsumptionDocument) -> str:
        if document.starts_on is None and document.ends_on is None:
            rango = "Todo el período"
        else:
            rango = f"Del {_day(document.starts_on)} al {_day(document.ends_on)}"
        return f"{rango} · Estado: {escape(document.status_label)}"

    def _table(self, document: ServiceConsumptionDocument, styles: object) -> Table | Paragraph:
        body = getSampleStyleSheet()["BodyText"]
        if not document.items:
            return Paragraph("No hay citas en el rango elegido.", body)
        rows: list[list[object]] = [["Servicio", "Precio", "Veces", "Ingreso estimado"]]
        rows.extend(
            [
                Paragraph(escape(item.name), body),
                f"S/ {item.price}",
                str(item.appointment_count),
                f"S/ {item.estimated_revenue}",
            ]
            for item in document.items
        )
        table = Table(rows, colWidths=[7.6 * cm, 3 * cm, 2.6 * cm, 4.2 * cm], repeatRows=1)
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
