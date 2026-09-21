"""Casos de uso de consentimientos, con repositorios en memoria."""

from __future__ import annotations

from dataclasses import replace

import pytest

from gestvet.core.activity import ActivityKind
from gestvet.modules.consents.domain.entities import (
    Consent,
    ConsentChannel,
    ConsentKind,
    ConsentStatus,
    ConsentTemplate,
)
from gestvet.modules.consents.domain.exceptions import (
    InvalidSignerName,
    PetNotOwned,
    TemplateNotFound,
    TemplateOutdated,
)
from gestvet.modules.consents.use_cases.accept_emergency_risk import (
    AcceptEmergencyRisk,
    AcceptEmergencyRiskCommand,
)
from gestvet.modules.consents.use_cases.record_in_person_emergency_risk import (
    RecordInPersonEmergencyRisk,
    RecordInPersonEmergencyRiskCommand,
)
from gestvet.modules.consents.use_cases.signing import RequestOrigin
from tests.conftest import RecordingActivity

CLIENTE = 4
MASCOTA = 3
PERSONAL = 9

VIGENTE = ConsentTemplate(
    id=2, kind=ConsentKind.EMERGENCY_RISK, version=2, title="Riesgo", body="Texto nuevo."
)
ANTERIOR = ConsentTemplate(
    id=1,
    kind=ConsentKind.EMERGENCY_RISK,
    version=1,
    title="Riesgo",
    body="Texto viejo.",
    is_active=False,
)


class InMemoryTemplates:
    def __init__(self, *templates: ConsentTemplate) -> None:
        self._templates = {template.id: template for template in templates}

    async def get(self, template_id: int) -> ConsentTemplate | None:
        return self._templates.get(template_id)

    async def current(self, kind: ConsentKind) -> ConsentTemplate | None:
        vigentes = [t for t in self._templates.values() if t.kind is kind and t.is_active]
        return max(vigentes, key=lambda t: t.version, default=None)


class InMemoryConsents:
    def __init__(self) -> None:
        self.saved: list[Consent] = []

    async def add(self, consent: Consent) -> Consent:
        guardado = replace(consent, id=len(self.saved) + 1)
        self.saved.append(guardado)
        return guardado

    async def get(self, consent_id: int) -> Consent | None:
        return next((c for c in self.saved if c.id == consent_id), None)


class OwnedPets:
    async def is_owned_by(self, pet_id: int, owner_id: int) -> bool:
        return (pet_id, owner_id) == (MASCOTA, CLIENTE)


def _online(**cambios: object) -> AcceptEmergencyRiskCommand:
    comando = AcceptEmergencyRiskCommand(
        client_id=CLIENTE,
        pet_id=MASCOTA,
        template_id=VIGENTE.id or 0,
        signer_name="Ana Quispe",
        origin=RequestOrigin(ip="10.0.0.1", user_agent="Firefox"),
    )
    return replace(comando, **cambios)


async def test_el_cliente_acepta_en_linea() -> None:
    consents, activity = InMemoryConsents(), RecordingActivity()
    use_case = AcceptEmergencyRisk(consents, InMemoryTemplates(VIGENTE), OwnedPets(), activity)

    firmado = await use_case(_online())

    assert firmado.status is ConsentStatus.ACCEPTED
    assert firmado.channel is ConsentChannel.ONLINE
    assert firmado.signer_user_id == CLIENTE
    assert firmado.witness_id is None
    assert firmado.template_id == VIGENTE.id
    assert firmado.text_snapshot == VIGENTE.render()
    assert (firmado.ip, firmado.user_agent) == ("10.0.0.1", "Firefox")
    assert activity.entries[0][:2] == (CLIENTE, ActivityKind.CONSENT_ACCEPTED)


async def test_no_se_firma_por_la_mascota_de_otro() -> None:
    use_case = AcceptEmergencyRisk(
        InMemoryConsents(), InMemoryTemplates(VIGENTE), OwnedPets(), RecordingActivity()
    )

    with pytest.raises(PetNotOwned):
        await use_case(_online(pet_id=99))


async def test_firmar_un_texto_reemplazado_pide_releerlo() -> None:
    consents = InMemoryConsents()
    use_case = AcceptEmergencyRisk(
        consents, InMemoryTemplates(VIGENTE, ANTERIOR), OwnedPets(), RecordingActivity()
    )

    with pytest.raises(TemplateOutdated):
        await use_case(_online(template_id=ANTERIOR.id))
    assert consents.saved == []


async def test_una_plantilla_inexistente_no_se_firma() -> None:
    use_case = AcceptEmergencyRisk(
        InMemoryConsents(), InMemoryTemplates(VIGENTE), OwnedPets(), RecordingActivity()
    )

    with pytest.raises(TemplateNotFound):
        await use_case(_online(template_id=404))


async def test_un_nombre_de_una_palabra_no_firma() -> None:
    consents = InMemoryConsents()
    use_case = AcceptEmergencyRisk(
        consents, InMemoryTemplates(VIGENTE), OwnedPets(), RecordingActivity()
    )

    with pytest.raises(InvalidSignerName):
        await use_case(_online(signer_name="Ana"))
    assert consents.saved == []


async def test_el_personal_registra_la_aceptacion_presencial_como_testigo() -> None:
    consents, activity = InMemoryConsents(), RecordingActivity()
    use_case = RecordInPersonEmergencyRisk(
        consents, InMemoryTemplates(VIGENTE), OwnedPets(), activity
    )

    firmado = await use_case(
        RecordInPersonEmergencyRiskCommand(
            staff_id=PERSONAL,
            client_id=CLIENTE,
            pet_id=MASCOTA,
            template_id=VIGENTE.id or 0,
            signer_name="  Rosa   Quispe ",
        )
    )

    assert firmado.channel is ConsentChannel.IN_PERSON
    assert firmado.witness_id == PERSONAL
    assert firmado.signer_user_id is None
    assert firmado.client_id == CLIENTE
    assert firmado.signer_name == "Rosa Quispe"
    assert activity.entries[0][:2] == (PERSONAL, ActivityKind.CONSENT_ACCEPTED)


async def test_en_el_mostrador_la_mascota_tiene_que_ser_del_cliente_indicado() -> None:
    use_case = RecordInPersonEmergencyRisk(
        InMemoryConsents(), InMemoryTemplates(VIGENTE), OwnedPets(), RecordingActivity()
    )

    with pytest.raises(PetNotOwned):
        await use_case(
            RecordInPersonEmergencyRiskCommand(
                staff_id=PERSONAL,
                client_id=77,
                pet_id=MASCOTA,
                template_id=VIGENTE.id or 0,
                signer_name="Rosa Quispe",
            )
        )
