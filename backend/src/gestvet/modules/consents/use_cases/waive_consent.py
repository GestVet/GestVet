"""Caso de uso: atender sin consentimiento por urgencia vital.

Nunca se frena la atención que salva la vida. Si el responsable no está y no
se lo puede ubicar, el veterinario deja constancia de que actuó sin
consentimiento y de por qué. Solo en una emergencia: una cita programada
siempre puede esperar la respuesta.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity import Principal
from gestvet.modules.consents.domain.entities import (
    Consent,
    ConsentKind,
    normalize_justification,
)
from gestvet.modules.consents.domain.exceptions import KindNotRequestable, TemplateNotFound
from gestvet.modules.consents.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.consents.ports.consent_repository import (
    ConsentRepository,
    ConsentTemplateRepository,
)
from gestvet.modules.consents.use_cases.appointment_access import appointment_for


@dataclass(frozen=True, slots=True)
class WaiveConsentCommand:
    veterinarian: Principal
    appointment_id: int
    kind: ConsentKind
    justification: str


class WaiveConsent:
    def __init__(
        self,
        consents: ConsentRepository,
        templates: ConsentTemplateRepository,
        appointments: AppointmentDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._consents = consents
        self._templates = templates
        self._appointments = appointments
        self._activity = activity

    async def __call__(self, command: WaiveConsentCommand, now: datetime | None = None) -> Consent:
        if not command.kind.requestable:
            raise KindNotRequestable()
        cita = await appointment_for(
            self._appointments, command.appointment_id, command.veterinarian
        )
        cita.ensure_open_for_consents()
        cita.ensure_emergency()
        justificacion = normalize_justification(command.justification)
        template = await self._templates.current(command.kind)
        if template is None:
            raise TemplateNotFound()

        guardado = await self._consents.add(
            Consent.waive(
                template,
                appointment_id=cita.id,
                pet_id=cita.pet_id,
                client_id=cita.client_id,
                recorded_by=command.veterinarian.user_id,
                justification=justificacion,
                now=now,
            )
        )
        await self._activity.record(
            command.veterinarian.user_id,
            ActivityKind.CONSENT_WAIVED,
            f"{guardado.kind.label}, cita {cita.id}",
        )
        return guardado
