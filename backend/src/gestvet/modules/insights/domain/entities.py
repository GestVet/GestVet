"""Entidades de dominio del panel de indicadores.

Python puro: nada de esto sabe de SQL ni de HTTP. Son proyecciones de solo
lectura calculadas a partir de datos que ya existen en otros módulos, no
información que este módulo posea o persista.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

# Sin vacuna hace más de un año, o sin control hace más de medio año: son
# umbrales genéricos, no un calendario de vacunación por especie, que sería
# otro proyecto. Sirven para "hace tiempo que no se ve a esta mascota", no
# para reemplazar el criterio del veterinario.
CARE_VACCINE_REMINDER_DAYS = 365
CARE_CHECKUP_REMINDER_DAYS = 180

# Una cita que sigue "pendiente" o "confirmada" mucho después de su hora, sin
# haberse completado ni cancelado, es la única señal indirecta de inasistencia
# que el sistema tiene hoy: no existe un estado "no asistió" que el personal
# pueda marcar. El margen de gracia evita marcar como inasistencia una cita
# que el personal todavía no tuvo tiempo de cerrar.
NO_SHOW_STALE_GRACE_HOURS = 3
NO_SHOW_HISTORY_WINDOW_DAYS = 180
NO_SHOW_UPCOMING_WINDOW_DAYS = 7
NO_SHOW_RISK_THRESHOLD = 2

# Ventana de pagos que se analiza, y cuántas muestras hace falta tener de un
# tipo de cita antes de confiar en su monto promedio.
PAYMENT_ANOMALY_WINDOW_DAYS = 30
PAYMENT_ANOMALY_MIN_SAMPLES = 3
PAYMENT_ANOMALY_DEVIATION = Decimal("0.5")

VETERINARIAN_ALERT_WINDOW_DAYS = 60
VETERINARIAN_ALERT_LOW_RATING_THRESHOLD = 3
VETERINARIAN_ALERT_COMPLAINT_THRESHOLD = 2

# Redefinido a propósito en vez de importado de `medical_records`: ese módulo
# no se puede importar acá (independencia entre módulos), y es el mismo
# criterio que ya usa este archivo con CARE_VACCINE_REMINDER_DAYS.
OVERVIEW_DUE_SOON_DAYS = 30


@dataclass(frozen=True, slots=True)
class CareReminder:
    pet_id: int
    pet_name: str
    owner_id: int
    owner_name: str
    reason: str
    last_occurred_at: datetime | None


@dataclass(frozen=True, slots=True)
class NoShowRisk:
    appointment_id: int
    client_id: int
    client_name: str
    pet_name: str
    scheduled_at: datetime
    past_incidents: int


@dataclass(frozen=True, slots=True)
class PaymentAnomaly:
    payment_id: int
    appointment_id: int
    client_id: int
    appointment_type_label: str
    amount: Decimal
    typical_amount: Decimal
    paid_at: datetime
    client_name: str = ""
    pet_name: str = ""


@dataclass(frozen=True, slots=True)
class VeterinarianAlert:
    veterinarian_id: int
    veterinarian_name: str
    low_rating_count: int
    complaint_count: int


# Registros crudos que llegan desde los puertos, antes de aplicar cualquier
# regla. Viven acá y no en `ports/` porque las reglas (en `rules.py`) los
# consumen, y el dominio no puede importar los puertos.


@dataclass(frozen=True, slots=True)
class PetCareRecord:
    pet_id: int
    pet_name: str
    owner_id: int
    owner_name: str
    registered_at: datetime
    last_vaccine_at: datetime | None
    last_checkup_at: datetime | None


VaccinationStatus = Literal["up_to_date", "due_soon", "overdue", "no_vaccines"]


@dataclass(frozen=True, slots=True)
class PetOverviewRecord:
    pet_id: int
    pet_name: str
    owner_id: int
    owner_name: str
    species: str
    breed: str
    sex: str | None
    birth_date: date
    weight_kg: Decimal | None
    is_active: bool
    last_vaccine_on: date | None
    next_vaccine_due_on: date | None
    vaccine_count: int


@dataclass(frozen=True, slots=True)
class PetOverview:
    pet_id: int
    pet_name: str
    owner_name: str
    species: str
    breed: str
    sex: str | None
    age_years: int
    weight_kg: Decimal | None
    is_active: bool
    vaccination_status: VaccinationStatus


@dataclass(frozen=True, slots=True)
class AppointmentRecord:
    appointment_id: int
    client_id: int
    client_name: str
    pet_name: str
    scheduled_at: datetime
    ends_at: datetime
    status: str


@dataclass(frozen=True, slots=True)
class PaymentRecord:
    payment_id: int
    appointment_id: int
    client_id: int
    appointment_type_id: int
    appointment_type_label: str
    is_emergency_type: bool
    amount: Decimal
    paid_at: datetime
    client_name: str = ""
    pet_name: str = ""


@dataclass(frozen=True, slots=True)
class VeterinarianSignal:
    veterinarian_id: int
    veterinarian_name: str
    low_rating_count: int
    complaint_count: int


@dataclass(frozen=True, slots=True)
class ServiceConsumptionRecord:
    appointment_type_id: int
    name: str
    is_emergency: bool
    price: Decimal
    appointment_count: int


@dataclass(frozen=True, slots=True)
class ServiceConsumption:
    appointment_type_id: int
    name: str
    is_emergency: bool
    price: Decimal
    appointment_count: int
    estimated_revenue: Decimal
