"""Casos de uso: el cliente acepta o rechaza en línea un pedido de consentimiento.

Solo el dueño del pedido, y solo mientras espera respuesta. Aceptar pide lo
mismo que cualquier firma: la casilla (la exige el contrato HTTP) y el nombre
completo. Rechazar no pide nombre: quien rechaza no firma nada.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.consents.domain.entities import Consent, ConsentChannel
from gestvet.modules.consents.domain.exceptions import ConsentNotFound
from gestvet.modules.consents.ports.consent_repository import ConsentRepository
from gestvet.modules.consents.use_cases.signing import RequestOrigin


@dataclass(frozen=True, slots=True)
class AcceptConsentCommand:
    consent_id: int
    client_id: int
    signer_name: str
    origin: RequestOrigin = RequestOrigin()


@dataclass(frozen=True, slots=True)
class DeclineConsentCommand:
    consent_id: int
    client_id: int
    reason: str | None = None
    origin: RequestOrigin = RequestOrigin()


async def _own_request(consents: ConsentRepository, consent_id: int, client_id: int) -> Consent:
    consent = await consents.get(consent_id)
    # Uno ajeno responde igual que uno inexistente; y uno firmado al abrir
    # una emergencia no es un pedido que se pueda responder.
    if consent is None or consent.client_id != client_id or consent.appointment_id is None:
        raise ConsentNotFound(consent_id)
    return consent


class AcceptConsent:
    def __init__(self, consents: ConsentRepository, activity: ActivityRecorder) -> None:
        self._consents = consents
        self._activity = activity

    async def __call__(self, command: AcceptConsentCommand, now: datetime | None = None) -> Consent:
        consent = await _own_request(self._consents, command.consent_id, command.client_id)
        consent.accept_request(
            signer_name=command.signer_name,
            channel=ConsentChannel.ONLINE,
            signer_user_id=command.client_id,
            ip=command.origin.ip,
            user_agent=command.origin.user_agent,
            now=now,
        )
        guardado = await self._consents.update(consent)
        await self._activity.record(
            command.client_id,
            ActivityKind.CONSENT_ACCEPTED,
            f"{guardado.kind.label}, cita {guardado.appointment_id}, en línea",
        )
        return guardado


class DeclineConsent:
    def __init__(self, consents: ConsentRepository, activity: ActivityRecorder) -> None:
        self._consents = consents
        self._activity = activity

    async def __call__(
        self, command: DeclineConsentCommand, now: datetime | None = None
    ) -> Consent:
        consent = await _own_request(self._consents, command.consent_id, command.client_id)
        consent.decline(
            reason=command.reason,
            signer_user_id=command.client_id,
            ip=command.origin.ip,
            user_agent=command.origin.user_agent,
            now=now,
        )
        guardado = await self._consents.update(consent)
        await self._activity.record(
            command.client_id,
            ActivityKind.CONSENT_DECLINED,
            f"{guardado.kind.label}, cita {guardado.appointment_id}",
        )
        return guardado
