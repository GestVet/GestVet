"""Pruebas de los avisos por WhatsApp. Con dobles en memoria, sin base ni servidor.

Verifican que el caso de uso llama al puerto con los datos correctos, no que
un mensaje real salga: eso lo decide el adaptador, que hoy es
`ConsoleWhatsAppSender` y mañana puede ser otro sin que estas pruebas cambien.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from gestvet.core.identity import Role
from gestvet.modules.appointments.domain.entities import Appointment, AppointmentStatus
from gestvet.modules.appointments.ports.client_directory import ClientContact
from gestvet.modules.appointments.use_cases.change_status import (
    ChangeAppointmentStatus,
    ChangeStatusCommand,
)
from gestvet.modules.appointments.use_cases.send_upcoming_reminders import (
    REMINDER_LEAD_TIME,
    SendUpcomingReminders,
)
from gestvet.modules.billing.domain.entities import Payment
from gestvet.modules.billing.domain.qr_charge import QrCharge
from gestvet.modules.billing.use_cases.confirm_qr_charge import (
    ConfirmQrCharge,
    ConfirmQrChargeCommand,
)
from tests.conftest import RecordingActivity

BASE = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)


class FakeAppointmentRepository:
    def __init__(self, appointments: list[Appointment]) -> None:
        self._by_id = {a.id: a for a in appointments}

    async def get(self, appointment_id: int) -> Appointment | None:
        return self._by_id.get(appointment_id)

    async def save(self, appointment: Appointment) -> Appointment:
        self._by_id[appointment.id] = appointment
        return appointment

    async def find_due_for_reminder(
        self, window_start: datetime, window_end: datetime
    ) -> list[Appointment]:
        return [
            a
            for a in self._by_id.values()
            if a.status is AppointmentStatus.CONFIRMED
            and a.reminder_sent_at is None
            and window_start <= a.scheduled_at < window_end
        ]


class FakeClientDirectory:
    def __init__(self, contacts: dict[int, ClientContact]) -> None:
        self._contacts = contacts

    async def find_contact(self, client_id: int) -> ClientContact | None:
        return self._contacts.get(client_id)


class FakePetDirectory:
    def __init__(self, names: dict[int, str]) -> None:
        self._names = names

    async def find_name(self, pet_id: int) -> str | None:
        return self._names.get(pet_id)


class RecordingWhatsAppSender:
    def __init__(self) -> None:
        self.confirmed: list[tuple[str, str, str, datetime]] = []
        self.reminders: list[tuple[str, str, str, datetime]] = []
        self.payments: list[tuple[str, str, Decimal]] = []
        self.vaccines: list[tuple[str, str, str, str, date]] = []

    async def send_appointment_confirmed(
        self, *, to: str, client_name: str, pet_name: str, scheduled_at: datetime
    ) -> None:
        self.confirmed.append((to, client_name, pet_name, scheduled_at))

    async def send_appointment_reminder(
        self, *, to: str, client_name: str, pet_name: str, scheduled_at: datetime
    ) -> None:
        self.reminders.append((to, client_name, pet_name, scheduled_at))

    async def send_payment_confirmed(self, *, to: str, client_name: str, amount: Decimal) -> None:
        self.payments.append((to, client_name, amount))

    async def send_vaccine_due_reminder(
        self, *, to: str, client_name: str, pet_name: str, vaccine_label: str, due_on: date
    ) -> None:
        self.vaccines.append((to, client_name, pet_name, vaccine_label, due_on))


def _appointment(**overrides: object) -> Appointment:
    valores: dict[str, object] = {
        "id": 1,
        "scheduled_at": BASE,
        "duration": timedelta(minutes=30),
        "client_id": 10,
        "pet_id": 5,
        "veterinarian_id": 20,
        "appointment_type_id": 1,
        "status": AppointmentStatus.PENDING,
    }
    valores.update(overrides)
    return Appointment(**valores)  # type: ignore[arg-type]


async def test_confirmar_una_cita_avisa_por_whatsapp() -> None:
    cita = _appointment()
    appointments = FakeAppointmentRepository([cita])
    clients = FakeClientDirectory({10: ClientContact(name="Ana Quispe", phone="987654321")})
    pets = FakePetDirectory({5: "Rocco"})
    whatsapp = RecordingWhatsAppSender()

    await ChangeAppointmentStatus(appointments, RecordingActivity(), clients, pets, whatsapp)(
        ChangeStatusCommand(
            appointment_id=1,
            actor_id=20,
            actor_role=Role.VETERINARIAN,
            target=AppointmentStatus.CONFIRMED,
        )
    )

    assert whatsapp.confirmed == [("987654321", "Ana Quispe", "Rocco", cita.scheduled_at)]


async def test_confirmar_no_avisa_si_el_cliente_no_tiene_telefono() -> None:
    cita = _appointment()
    appointments = FakeAppointmentRepository([cita])
    clients = FakeClientDirectory({10: ClientContact(name="Ana Quispe", phone="")})
    whatsapp = RecordingWhatsAppSender()

    await ChangeAppointmentStatus(
        appointments, RecordingActivity(), clients, FakePetDirectory({}), whatsapp
    )(
        ChangeStatusCommand(
            appointment_id=1,
            actor_id=20,
            actor_role=Role.VETERINARIAN,
            target=AppointmentStatus.CONFIRMED,
        )
    )

    assert whatsapp.confirmed == []


async def test_completar_no_avisa_por_whatsapp() -> None:
    """Solo la confirmación dispara el aviso; completar no repite el mensaje."""
    cita = _appointment(status=AppointmentStatus.CONFIRMED)
    appointments = FakeAppointmentRepository([cita])
    clients = FakeClientDirectory({10: ClientContact(name="Ana Quispe", phone="987654321")})
    whatsapp = RecordingWhatsAppSender()

    await ChangeAppointmentStatus(
        appointments, RecordingActivity(), clients, FakePetDirectory({5: "Rocco"}), whatsapp
    )(
        ChangeStatusCommand(
            appointment_id=1,
            actor_id=20,
            actor_role=Role.VETERINARIAN,
            target=AppointmentStatus.COMPLETED,
        )
    )

    assert whatsapp.confirmed == []


class FakeQrChargeRepository:
    def __init__(self, charge: QrCharge) -> None:
        self._charge = charge

    async def get(self, charge_id: int) -> QrCharge | None:
        return self._charge if self._charge.id == charge_id else None

    async def save(self, charge: QrCharge) -> QrCharge:
        self._charge = charge
        return charge


class FakePaymentRepository:
    async def add(self, payment: Payment) -> Payment:
        payment.id = 1
        return payment


async def test_confirmar_un_qr_avisa_por_whatsapp() -> None:
    charge = QrCharge(
        id=1,
        appointment_id=3,
        client_id=10,
        amount=Decimal("50.00"),
        gateway_charge_id="sandbox-1",
        qr_image_data_url="data:image/png;base64,",
    )
    clients = FakeClientDirectory({10: ClientContact(name="Ana Quispe", phone="987654321")})
    whatsapp = RecordingWhatsAppSender()

    await ConfirmQrCharge(
        FakeQrChargeRepository(charge),
        FakePaymentRepository(),
        RecordingActivity(),
        clients,
        whatsapp,
    )(ConfirmQrChargeCommand(charge_id=1, requester_id=10, is_staff=False))

    assert whatsapp.payments == [("987654321", "Ana Quispe", Decimal("50.00"))]


async def test_send_upcoming_reminders_avisa_y_marca_la_cita() -> None:
    ahora = BASE
    cita = _appointment(
        scheduled_at=ahora + REMINDER_LEAD_TIME + timedelta(minutes=10),
        status=AppointmentStatus.CONFIRMED,
    )
    appointments = FakeAppointmentRepository([cita])
    clients = FakeClientDirectory({10: ClientContact(name="Ana Quispe", phone="987654321")})
    pets = FakePetDirectory({5: "Rocco"})
    whatsapp = RecordingWhatsAppSender()

    resultados = await SendUpcomingReminders(appointments, clients, pets, whatsapp)(now=ahora)

    assert [r.notified for r in resultados] == [True]
    assert whatsapp.reminders == [("987654321", "Ana Quispe", "Rocco", cita.scheduled_at)]
    assert cita.reminder_sent_at == ahora


async def test_send_upcoming_reminders_no_repite_una_cita_ya_avisada() -> None:
    ahora = BASE
    cita = _appointment(
        scheduled_at=ahora + REMINDER_LEAD_TIME + timedelta(minutes=10),
        status=AppointmentStatus.CONFIRMED,
        reminder_sent_at=ahora - timedelta(hours=1),
    )
    appointments = FakeAppointmentRepository([cita])
    whatsapp = RecordingWhatsAppSender()

    resultados = await SendUpcomingReminders(
        appointments, FakeClientDirectory({}), FakePetDirectory({}), whatsapp
    )(now=ahora)

    assert resultados == []
    assert whatsapp.reminders == []


async def test_send_upcoming_reminders_ignora_citas_fuera_de_la_ventana() -> None:
    ahora = BASE
    lejos = _appointment(
        id=1, scheduled_at=ahora + timedelta(hours=1), status=AppointmentStatus.CONFIRMED
    )
    appointments = FakeAppointmentRepository([lejos])
    whatsapp = RecordingWhatsAppSender()

    resultados = await SendUpcomingReminders(
        appointments, FakeClientDirectory({}), FakePetDirectory({}), whatsapp
    )(now=ahora)

    assert resultados == []


@pytest.mark.parametrize("estado", [AppointmentStatus.PENDING, AppointmentStatus.COMPLETED])
async def test_send_upcoming_reminders_solo_mira_citas_confirmadas(
    estado: AppointmentStatus,
) -> None:
    ahora = BASE
    cita = _appointment(
        scheduled_at=ahora + REMINDER_LEAD_TIME + timedelta(minutes=10), status=estado
    )
    appointments = FakeAppointmentRepository([cita])
    whatsapp = RecordingWhatsAppSender()

    resultados = await SendUpcomingReminders(
        appointments, FakeClientDirectory({}), FakePetDirectory({}), whatsapp
    )(now=ahora)

    assert resultados == []
