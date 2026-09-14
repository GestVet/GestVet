"""La hora de la clínica.

La clínica opera en un único local, en Trujillo, sin horario de verano: el
desplazamiento es un dato del negocio, no una preferencia de quien mira la
pantalla. Lo necesitan la agenda y las citas por igual, así que vive en el
núcleo y ningún módulo tiene que importar a otro para saber qué día es.

Python puro: lo importa también la capa de dominio.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

CLINIC_UTC_OFFSET = timedelta(hours=-5)


def clinic_date(moment: datetime) -> date:
    """El día calendario de la clínica en el que cae un instante."""
    return (moment + CLINIC_UTC_OFFSET).date()


def clinic_midnight(day: date) -> datetime:
    """El comienzo, en UTC, de un día calendario de la clínica."""
    return datetime.combine(day, time.min, tzinfo=UTC) - CLINIC_UTC_OFFSET


def clinic_day_window(moment: datetime) -> tuple[datetime, datetime]:
    """Ventana en UTC del día calendario de la clínica que contiene `moment`.

    Comparar fechas de calendario en UTC directamente rompe cerca de la
    medianoche: una cita de las 20:00 en Trujillo cae en el día siguiente en
    UTC, y "todo ese día" dejaría de incluirla.
    """
    starts_at = clinic_midnight(clinic_date(moment))
    return starts_at, starts_at + timedelta(days=1)
