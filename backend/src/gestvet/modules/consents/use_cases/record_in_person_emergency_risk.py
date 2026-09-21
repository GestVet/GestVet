"""Caso de uso: el personal registra en el mostrador que el responsable aceptó.

Quien llega sin cuenta no puede firmar en línea. Lee el texto en la pantalla
del mostrador (o se lo leen), escribe o dicta su nombre, y el personal deja
constancia como testigo. La firma no la hace el personal: el nombre es el del
responsable, y el personal queda como quien lo presenció.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.consents.domain.entities import Consent, ConsentChannel, ConsentKind
from gestvet.modules.consents.ports.consent_repository import (
    ConsentRepository,
    ConsentTemplateRepository,
)
from gestvet.modules.consents.ports.pet_directory import PetDirectory
from gestvet.modules.consents.use_cases.signing import (
    RequestOrigin,
    ensure_pet_of,
    template_to_sign,
)


@dataclass(frozen=True, slots=True)
class RecordInPersonEmergencyRiskCommand:
    staff_id: int
    client_id: int
    pet_id: int
    template_id: int
    signer_name: str
    origin: RequestOrigin = RequestOrigin()


class RecordInPersonEmergencyRisk:
    def __init__(
        self,
        consents: ConsentRepository,
        templates: ConsentTemplateRepository,
        pets: PetDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._consents = consents
        self._templates = templates
        self._pets = pets
        self._activity = activity

    async def __call__(self, command: RecordInPersonEmergencyRiskCommand) -> Consent:
        await ensure_pet_of(self._pets, command.pet_id, command.client_id)
        template = await template_to_sign(
            self._templates, command.template_id, ConsentKind.EMERGENCY_RISK
        )
        guardado = await self._consents.add(
            Consent.accept(
                template,
                pet_id=command.pet_id,
                client_id=command.client_id,
                channel=ConsentChannel.IN_PERSON,
                signer_name=command.signer_name,
                witness_id=command.staff_id,
                ip=command.origin.ip,
                user_agent=command.origin.user_agent,
            )
        )
        await self._activity.record(
            command.staff_id,
            ActivityKind.CONSENT_ACCEPTED,
            f"{guardado.kind.label}, mascota {guardado.pet_id}, "
            f"cliente {guardado.client_id}, presencial",
        )
        return guardado
