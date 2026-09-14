"""Recordatorios de vacunas por WhatsApp: el caso de uso con dobles y la consulta real."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.medical_records.adapters.persistence.directories import (
    SqlOwnerContactDirectory,
)
from gestvet.modules.medical_records.adapters.persistence.repositories import (
    SqlAlchemyVaccinationRepository,
)
from gestvet.modules.medical_records.domain.vaccination import Vaccination, VaccineCode
from gestvet.modules.medical_records.ports.owner_contact_directory import OwnerContact
from gestvet.modules.medical_records.use_cases.send_vaccine_reminders import SendVaccineReminders
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import build_pet, build_user
from tests.test_whatsapp_notifications import RecordingWhatsAppSender

HOY = date(2026, 9, 14)
# Las 10:00 en la clínica, dentro del horario de avisos.
EN_HORARIO = datetime(2026, 9, 14, 15, 0, tzinfo=UTC)
ANA = OwnerContact(owner_name="Ana Quispe", phone="987654321", pet_name="Rocco")


class FakeVaccinationRepository:
    def __init__(self, vaccinations: list[Vaccination]) -> None:
        self._vaccinations = vaccinations
        self.marked: dict[int, datetime] = {}

    async def find_due_for_reminder(self, first_day: date, last_day: date) -> list[Vaccination]:
        return [
            item
            for item in self._vaccinations
            if item.next_due_on is not None
            and first_day <= item.next_due_on <= last_day
            and item.id not in self.marked
        ]

    async def mark_reminder_sent(self, vaccination_id: int, sent_at: datetime) -> None:
        self.marked[vaccination_id] = sent_at


class FakeOwnerContacts:
    def __init__(self, contacts: dict[int, OwnerContact]) -> None:
        self._contacts = contacts

    async def contact_for_pet(self, pet_id: int) -> OwnerContact | None:
        return self._contacts.get(pet_id)


def _rabia(vaccination_id: int, next_due_on: date) -> Vaccination:
    return Vaccination(
        id=vaccination_id,
        pet_id=5,
        veterinarian_id=1,
        vaccine=VaccineCode.RABIES,
        applied_on=date(2025, 9, 20),
        next_due_on=next_due_on,
    )


async def test_avisa_una_semana_antes_y_no_repite_el_mensaje() -> None:
    vacunas = FakeVaccinationRepository(
        [_rabia(1, HOY + timedelta(days=5)), _rabia(2, HOY + timedelta(days=20))]
    )
    whatsapp = RecordingWhatsAppSender()
    avisar = SendVaccineReminders(vacunas, FakeOwnerContacts({5: ANA}), whatsapp)

    resultados = await avisar(now=EN_HORARIO)

    assert [(r.vaccination_id, r.notified) for r in resultados] == [(1, True)]
    assert whatsapp.vaccines == [
        ("987654321", "Ana Quispe", "Rocco", "Antirrábica", HOY + timedelta(days=5))
    ]
    assert vacunas.marked == {1: EN_HORARIO}
    assert await avisar(now=EN_HORARIO + timedelta(minutes=30)) == []


async def test_no_avisa_de_madrugada() -> None:
    vacunas = FakeVaccinationRepository([_rabia(1, HOY + timedelta(days=5))])
    whatsapp = RecordingWhatsAppSender()

    # Las 02:00 en la clínica.
    madrugada = datetime(2026, 9, 14, 7, 0, tzinfo=UTC)
    resultados = await SendVaccineReminders(vacunas, FakeOwnerContacts({5: ANA}), whatsapp)(
        now=madrugada
    )

    assert resultados == []
    assert vacunas.marked == {}


async def test_sin_telefono_se_marca_sin_mandar_nada() -> None:
    vacunas = FakeVaccinationRepository([_rabia(1, HOY + timedelta(days=5))])
    whatsapp = RecordingWhatsAppSender()
    sin_telefono = OwnerContact(owner_name="Ana Quispe", phone="", pet_name="Rocco")

    resultados = await SendVaccineReminders(
        vacunas, FakeOwnerContacts({5: sin_telefono}), whatsapp
    )(now=EN_HORARIO)

    assert [r.notified for r in resultados] == [False]
    assert whatsapp.vaccines == []
    assert vacunas.marked == {1: EN_HORARIO}


async def test_la_consulta_toma_solo_la_ultima_dosis_sin_aviso(session: AsyncSession) -> None:
    users = SqlAlchemyUserRepository(session)
    dueno = await users.add(build_user("ana@example.com", phone="987654321"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()
    mascota = await SqlAlchemyPetRepository(session).add(build_pet(owner_id=dueno.id or 0))
    repositorio = SqlAlchemyVaccinationRepository(session)

    def dosis(
        vaccine: VaccineCode, applied_on: date, next_due_on: date, product_name: str = ""
    ) -> Vaccination:
        return Vaccination(
            pet_id=mascota.id or 0,
            veterinarian_id=veterinario.id or 0,
            vaccine=vaccine,
            applied_on=applied_on,
            next_due_on=next_due_on,
            product_name=product_name,
        )

    por_vencer = await repositorio.add(
        dosis(VaccineCode.RABIES, date(2025, 9, 18), HOY + timedelta(days=4))
    )
    # Ya se puso el refuerzo: la dosis anterior no se avisa.
    await repositorio.add(dosis(VaccineCode.DEWORMING, date(2026, 6, 10), HOY + timedelta(days=2)))
    await repositorio.add(dosis(VaccineCode.DEWORMING, date(2026, 9, 1), date(2026, 11, 30)))
    # Dos "otra vacuna" con productos distintos no se pisan entre sí.
    otra = await repositorio.add(
        dosis(VaccineCode.OTHER, date(2025, 9, 20), HOY + timedelta(days=5), "Giardia")
    )
    await repositorio.add(
        dosis(VaccineCode.OTHER, date(2026, 9, 1), date(2027, 9, 1), "Leptospira")
    )
    # Fuera de la semana.
    await repositorio.add(
        dosis(VaccineCode.DOG_MULTIVALENT, date(2025, 10, 1), HOY + timedelta(days=20))
    )
    # Ya avisada.
    avisada = await repositorio.add(
        dosis(VaccineCode.DOG_KENNEL_COUGH, date(2025, 9, 15), HOY + timedelta(days=3))
    )
    await repositorio.mark_reminder_sent(avisada.id or 0, EN_HORARIO)
    await session.commit()

    pendientes = await repositorio.find_due_for_reminder(HOY, HOY + timedelta(days=7))

    assert [item.id for item in pendientes] == [por_vencer.id, otra.id]


async def test_no_se_avisa_por_una_mascota_de_baja(session: AsyncSession) -> None:
    dueno = await SqlAlchemyUserRepository(session).add(
        build_user("ana@example.com", phone="987654321")
    )
    await session.flush()
    pets = SqlAlchemyPetRepository(session)
    activa = await pets.add(build_pet(owner_id=dueno.id or 0))
    de_baja = await pets.add(build_pet(owner_id=dueno.id or 0, name="Luna", is_active=False))
    await session.commit()
    contactos = SqlOwnerContactDirectory(session)

    assert await contactos.contact_for_pet(activa.id or 0) == ANA
    assert await contactos.contact_for_pet(de_baja.id or 0) is None
