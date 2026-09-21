"""Caso de uso: el responsable firma un pedido en la pantalla del veterinario.

El veterinario le pasa el dispositivo: el responsable lee el texto, marca la
casilla y escribe su nombre. La firma es del responsable; el veterinario queda
como testigo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity import Principal
from gestvet.modules.consents.domain.entities import Consent, ConsentChannel
from gestvet.modules.consents.domain.exceptions import AppointmentNotFound, ConsentNotFound
from gestvet.modules.consents.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.consents.ports.consent_repository import ConsentRepository
from gestvet.modules.consents.use_cases.appointment_access import appointment_for
from gestvet.modules.consents.use_cases.signing import RequestOrigin


@dataclass(frozen=True, slots=True)
class AcceptConsentInPersonCommand:
    consent_id: int
    witness: Principal
    signer_name: str
    origin: RequestOrigin = RequestOrigin()


class AcceptConsentInPerson:
    def __init__(
        self,
        consents: ConsentRepository,
        appointments: AppointmentDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._consents = consents
        self._appointments = appointments
        self._activity = activity

    async def __call__(
        self, command: AcceptConsentInPersonCommand, now: datetime | None = None
    ) -> Consent:
        consent = await self._consents.get(command.consent_id)
        if consent is None or consent.appointment_id is None:
            raise ConsentNotFound(command.consent_id)
        try:
            await appointment_for(self._appointments, consent.appointment_id, command.witness)
        except AppointmentNotFound as error:
            raise ConsentNotFound(command.consent_id) from error

        consent.accept_request(
            signer_name=command.signer_name,
            channel=ConsentChannel.IN_PERSON,
            witness_id=command.witness.user_id,
            ip=command.origin.ip,
            user_agent=command.origin.user_agent,
            now=now,
        )
        guardado = await self._consents.update(consent)
        await self._activity.record(
            command.witness.user_id,
            ActivityKind.CONSENT_ACCEPTED,
            f"{guardado.kind.label}, cita {guardado.appointment_id}, presencial",
        )
        return guardado
