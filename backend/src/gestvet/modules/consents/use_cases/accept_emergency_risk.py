"""Caso de uso: el cliente acepta en línea el riesgo de una emergencia.

Es lo único que se le pide antes de abrirla. Nunca frena la atención que
salva la vida: no pide detalle de nada, solo que el dueño sepa que el animal
puede estar grave y que el costo se conoce al final.
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
class AcceptEmergencyRiskCommand:
    client_id: int
    pet_id: int
    template_id: int
    signer_name: str
    origin: RequestOrigin = RequestOrigin()


class AcceptEmergencyRisk:
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

    async def __call__(self, command: AcceptEmergencyRiskCommand) -> Consent:
        await ensure_pet_of(self._pets, command.pet_id, command.client_id)
        template = await template_to_sign(
            self._templates, command.template_id, ConsentKind.EMERGENCY_RISK
        )
        guardado = await self._consents.add(
            Consent.accept(
                template,
                pet_id=command.pet_id,
                client_id=command.client_id,
                channel=ConsentChannel.ONLINE,
                signer_name=command.signer_name,
                signer_user_id=command.client_id,
                ip=command.origin.ip,
                user_agent=command.origin.user_agent,
            )
        )
        await self._activity.record(
            command.client_id,
            ActivityKind.CONSENT_ACCEPTED,
            f"{guardado.kind.label}, mascota {guardado.pet_id}, en línea",
        )
        return guardado
