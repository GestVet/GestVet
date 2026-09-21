"""Casos de uso de los consentimientos que pide el veterinario, con dobles en memoria."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from gestvet.core.activity import ActivityKind
from gestvet.core.identity import Principal, Role
from gestvet.modules.consents.domain.appointment_facts import AppointmentFacts
from gestvet.modules.consents.domain.entities import (
    Consent,
    ConsentChannel,
    ConsentKind,
    ConsentStatus,
    ConsentTemplate,
)
from gestvet.modules.consents.domain.exceptions import (
    AppointmentCancelled,
    AppointmentNotFound,
    AppointmentRequired,
    ConsentExpired,
    ConsentNotFound,
    ConsentNotPending,
    InvalidConsentDetails,
    InvalidWaiver,
    KindNotRequestable,
    PendingRequestExists,
    WaiverOnlyForEmergencies,
)
from gestvet.modules.consents.use_cases.accept_consent_in_person import (
    AcceptConsentInPerson,
    AcceptConsentInPersonCommand,
)
from gestvet.modules.consents.use_cases.read_consents import ConsentQuery, ListConsents
from gestvet.modules.consents.use_cases.request_consent import (
    RequestConsent,
    RequestConsentCommand,
)
from gestvet.modules.consents.use_cases.respond_to_consent import (
    AcceptConsent,
    AcceptConsentCommand,
    DeclineConsent,
    DeclineConsentCommand,
)
from gestvet.modules.consents.use_cases.waive_consent import WaiveConsent, WaiveConsentCommand
from tests.conftest import RecordingActivity

AHORA = datetime(2026, 9, 21, 15, 0, tzinfo=UTC)
CLIENTE, OTRO_CLIENTE, MASCOTA = 4, 5, 3
VETERINARIO = Principal(user_id=9, role=Role.VETERINARIAN, is_active=True)
OTRO_VETERINARIO = Principal(user_id=8, role=Role.VETERINARIAN, is_active=True)
ADMIN = Principal(user_id=1, role=Role.ADMIN, is_active=True)
CITA, EMERGENCIA, CANCELADA = 10, 11, 12
JUSTIFICACION = "Paro respiratorio; el responsable no contesta el teléfono."

PLANTILLAS = {
    kind: ConsentTemplate(id=index, kind=kind, version=1, title=kind.label, body="Autorizo.")
    for index, kind in enumerate(ConsentKind, start=1)
}


class InMemoryTemplates:
    async def get(self, template_id: int) -> ConsentTemplate | None:
        return next((t for t in PLANTILLAS.values() if t.id == template_id), None)

    async def current(self, kind: ConsentKind) -> ConsentTemplate | None:
        return PLANTILLAS.get(kind)


class InMemoryConsents:
    def __init__(self) -> None:
        self.saved: dict[int, Consent] = {}

    async def add(self, consent: Consent) -> Consent:
        guardado = replace(consent, id=len(self.saved) + 1)
        self.saved[guardado.id or 0] = guardado
        return deepcopy(guardado)

    async def get(self, consent_id: int) -> Consent | None:
        encontrado = self.saved.get(consent_id)
        return deepcopy(encontrado) if encontrado else None

    async def update(self, consent: Consent) -> Consent:
        self.saved[consent.id or 0] = deepcopy(consent)
        return consent

    async def list_for_appointment(self, appointment_id: int) -> list[Consent]:
        return [c for c in self.saved.values() if c.appointment_id == appointment_id][::-1]

    async def list_for_client(self, client_id: int) -> list[Consent]:
        return [
            c
            for c in self.saved.values()
            if c.client_id == client_id and c.appointment_id is not None
        ][::-1]


class Appointments:
    _CITAS = {
        CITA: AppointmentFacts(CITA, CLIENTE, MASCOTA, VETERINARIO.user_id, "confirmed", False),
        EMERGENCIA: AppointmentFacts(
            EMERGENCIA, CLIENTE, MASCOTA, VETERINARIO.user_id, "pending", True
        ),
        CANCELADA: AppointmentFacts(
            CANCELADA, CLIENTE, MASCOTA, VETERINARIO.user_id, "cancelled", True
        ),
    }

    async def find(self, appointment_id: int) -> AppointmentFacts | None:
        return self._CITAS.get(appointment_id)


class Clinica:
    def __init__(self) -> None:
        self.consents = InMemoryConsents()
        self.activity = RecordingActivity()

    async def pedir(
        self,
        kind: ConsentKind = ConsentKind.PROCEDURE,
        *,
        cita: int = CITA,
        quien: Principal = VETERINARIO,
        now: datetime = AHORA,
        procedure: str | None = "Castración",
    ) -> Consent:
        return await RequestConsent(
            self.consents, InMemoryTemplates(), Appointments(), self.activity
        )(
            RequestConsentCommand(
                requester=quien,
                appointment_id=cita,
                kind=kind,
                procedure=procedure,
                estimated_cost=Decimal("300"),
            ),
            now=now,
        )

    async def aceptar(self, consent_id: int, *, cliente: int = CLIENTE, now: datetime) -> Consent:
        return await AcceptConsent(self.consents, self.activity)(
            AcceptConsentCommand(
                consent_id=consent_id, client_id=cliente, signer_name="Ana Quispe"
            ),
            now=now,
        )

    async def eximir(
        self, *, cita: int = EMERGENCIA, justificacion: str = JUSTIFICACION
    ) -> Consent:
        return await WaiveConsent(
            self.consents, InMemoryTemplates(), Appointments(), self.activity
        )(
            WaiveConsentCommand(
                veterinarian=VETERINARIO,
                appointment_id=cita,
                kind=ConsentKind.HOSPITALIZATION,
                justification=justificacion,
            ),
            now=AHORA,
        )


async def test_el_veterinario_pide_y_queda_pendiente_para_el_dueno() -> None:
    clinica = Clinica()

    pedido = await clinica.pedir()

    assert pedido.status is ConsentStatus.PENDING
    assert (pedido.client_id, pedido.pet_id, pedido.appointment_id) == (CLIENTE, MASCOTA, CITA)
    assert pedido.requested_by == VETERINARIO.user_id
    assert "S/ 300.00" in pedido.text_snapshot
    assert clinica.activity.entries[0][:2] == (
        VETERINARIO.user_id,
        ActivityKind.CONSENT_REQUESTED,
    )


async def test_el_procedimiento_es_obligatorio_segun_el_tipo() -> None:
    clinica = Clinica()
    with pytest.raises(InvalidConsentDetails):
        await clinica.pedir(ConsentKind.EUTHANASIA, procedure=None)
    assert (await clinica.pedir(ConsentKind.HOSPITALIZATION, procedure=None)).details


async def test_no_se_pide_sobre_la_cita_de_otro_ni_una_cancelada() -> None:
    clinica = Clinica()
    with pytest.raises(AppointmentNotFound):
        await clinica.pedir(quien=OTRO_VETERINARIO)
    with pytest.raises(AppointmentNotFound):
        await clinica.pedir(cita=404)
    with pytest.raises(AppointmentCancelled):
        await clinica.pedir(cita=CANCELADA)
    with pytest.raises(KindNotRequestable):
        await clinica.pedir(ConsentKind.EMERGENCY_RISK)


async def test_no_hay_dos_pedidos_iguales_abiertos() -> None:
    clinica = Clinica()
    await clinica.pedir()

    with pytest.raises(PendingRequestExists):
        await clinica.pedir()
    await clinica.pedir(ConsentKind.ANESTHESIA)
    # Vencido el primero, se puede volver a pedir.
    assert await clinica.pedir(now=AHORA + timedelta(hours=25))


async def test_el_dueno_acepta_en_linea() -> None:
    clinica = Clinica()
    pedido = await clinica.pedir()

    firmado = await clinica.aceptar(pedido.id or 0, now=AHORA + timedelta(hours=2))

    assert firmado.status is ConsentStatus.ACCEPTED
    assert firmado.channel is ConsentChannel.ONLINE
    assert firmado.signer_user_id == CLIENTE
    assert clinica.consents.saved[pedido.id or 0].status is ConsentStatus.ACCEPTED
    assert clinica.activity.entries[-1][:2] == (CLIENTE, ActivityKind.CONSENT_ACCEPTED)


async def test_otro_cliente_no_responde_un_pedido_ajeno() -> None:
    clinica = Clinica()
    pedido = await clinica.pedir()

    with pytest.raises(ConsentNotFound):
        await clinica.aceptar(pedido.id or 0, cliente=OTRO_CLIENTE, now=AHORA)
    with pytest.raises(ConsentNotFound):
        await DeclineConsent(clinica.consents, clinica.activity)(
            DeclineConsentCommand(consent_id=pedido.id or 0, client_id=OTRO_CLIENTE)
        )


async def test_un_pedido_vencido_o_respondido_no_se_responde() -> None:
    clinica = Clinica()
    pedido = await clinica.pedir()

    with pytest.raises(ConsentExpired):
        await clinica.aceptar(pedido.id or 0, now=AHORA + timedelta(hours=24, seconds=1))

    rechazado = await DeclineConsent(clinica.consents, clinica.activity)(
        DeclineConsentCommand(consent_id=pedido.id or 0, client_id=CLIENTE, reason="Lo pienso"),
        now=AHORA + timedelta(hours=1),
    )
    assert rechazado.status is ConsentStatus.DECLINED
    assert rechazado.decision_reason == "Lo pienso"
    assert clinica.activity.entries[-1][:2] == (CLIENTE, ActivityKind.CONSENT_DECLINED)
    with pytest.raises(ConsentNotPending):
        await clinica.aceptar(pedido.id or 0, now=AHORA + timedelta(hours=2))


async def test_el_responsable_firma_en_persona_con_el_veterinario_de_testigo() -> None:
    clinica = Clinica()
    pedido = await clinica.pedir()
    use_case = AcceptConsentInPerson(clinica.consents, Appointments(), clinica.activity)

    with pytest.raises(ConsentNotFound):
        await use_case(
            AcceptConsentInPersonCommand(
                consent_id=pedido.id or 0, witness=OTRO_VETERINARIO, signer_name="Ana Quispe"
            ),
            now=AHORA,
        )
    firmado = await use_case(
        AcceptConsentInPersonCommand(
            consent_id=pedido.id or 0, witness=VETERINARIO, signer_name="Ana Quispe"
        ),
        now=AHORA,
    )

    assert firmado.channel is ConsentChannel.IN_PERSON
    assert firmado.witness_id == VETERINARIO.user_id
    assert firmado.signer_user_id is None


async def test_la_urgencia_vital_solo_en_emergencias() -> None:
    clinica = Clinica()

    with pytest.raises(WaiverOnlyForEmergencies):
        await clinica.eximir(cita=CITA)
    with pytest.raises(AppointmentCancelled):
        await clinica.eximir(cita=CANCELADA)
    with pytest.raises(InvalidWaiver):
        await clinica.eximir(justificacion="Muy urgente")

    eximido = await clinica.eximir()
    assert eximido.status is ConsentStatus.WAIVED_EMERGENCY
    assert eximido.decision_reason == JUSTIFICACION
    assert clinica.activity.entries[-1][:2] == (VETERINARIO.user_id, ActivityKind.CONSENT_WAIVED)


async def test_el_listado_se_recorta_por_quien_pregunta() -> None:
    clinica = Clinica()
    pedido = await clinica.pedir()
    await clinica.eximir()
    listar = ListConsents(clinica.consents, Appointments())
    cliente = Principal(user_id=CLIENTE, role=Role.CLIENT, is_active=True)

    todos = await listar(ConsentQuery(), cliente, now=AHORA)
    assert [c.id for c in todos.items] == [2, 1]
    assert todos.appointment_is_emergency is None
    pendientes = await listar(ConsentQuery(status=ConsentStatus.PENDING), cliente, now=AHORA)
    assert [c.id for c in pendientes.items] == [pedido.id]
    vencidos = await listar(
        ConsentQuery(status=ConsentStatus.PENDING), cliente, now=AHORA + timedelta(days=2)
    )
    assert vencidos.items == []
    ajeno = Principal(user_id=OTRO_CLIENTE, role=Role.CLIENT, is_active=True)
    assert (await listar(ConsentQuery(), ajeno)).items == []

    de_la_cita = await listar(ConsentQuery(appointment_id=CITA), VETERINARIO)
    assert len(de_la_cita.items) == 1
    assert de_la_cita.appointment_is_emergency is False
    de_la_emergencia = await listar(ConsentQuery(appointment_id=EMERGENCIA), ADMIN)
    assert len(de_la_emergencia.items) == 1
    assert de_la_emergencia.appointment_is_emergency is True
    with pytest.raises(AppointmentNotFound):
        await listar(ConsentQuery(appointment_id=CITA), OTRO_VETERINARIO)
    with pytest.raises(AppointmentRequired):
        await listar(ConsentQuery(), VETERINARIO)
