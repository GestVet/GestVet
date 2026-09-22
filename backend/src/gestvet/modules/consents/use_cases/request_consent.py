"""Caso de uso: el veterinario pide un consentimiento específico sobre una cita.

Lo pide después de evaluar a la mascota, con el detalle de lo que propone. El
dueño lo responde desde su cuenta o en persona, en la pantalla del
veterinario. Mientras tanto queda pendiente, y vence solo a las 24 horas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity import Principal
from gestvet.modules.consents.domain.details import ConsentDetails
from gestvet.modules.consents.domain.entities import Consent, ConsentKind, ConsentStatus
from gestvet.modules.consents.domain.exceptions import (
    KindNotRequestable,
    PendingRequestExists,
    TemplateNotFound,
)
from gestvet.modules.consents.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.consents.ports.consent_repository import (
    ConsentRepository,
    ConsentTemplateRepository,
)
from gestvet.modules.consents.use_cases.appointment_access import appointment_for


@dataclass(frozen=True, slots=True)
class RequestConsentCommand:
    requester: Principal
    appointment_id: int
    kind: ConsentKind
    procedure: str | None = None
    prognosis: str | None = None
    estimated_cost: Decimal | None = None
    notes: str | None = None


class RequestConsent:
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

    async def __call__(
        self, command: RequestConsentCommand, now: datetime | None = None
    ) -> Consent:
        momento = now or datetime.now(UTC)
        if not command.kind.requestable:
            raise KindNotRequestable()
        cita = await appointment_for(self._appointments, command.appointment_id, command.requester)
        cita.ensure_open_for_consents()
        details = ConsentDetails.build(
            procedure=command.procedure,
            prognosis=command.prognosis,
            estimated_cost=command.estimated_cost,
            notes=command.notes,
            procedure_required=command.kind.requires_procedure,
        )
        # Dos pedidos iguales abiertos a la vez confunden al dueño: no sabría
        # cuál firmar. Uno vencido o ya respondido no cuenta.
        for previo in await self._consents.list_for_appointment(cita.id):
            if (
                previo.kind is command.kind
                and previo.effective_status(momento) is ConsentStatus.PENDING
            ):
                raise PendingRequestExists()
        template = await self._templates.current(command.kind)
        if template is None:
            raise TemplateNotFound()

        guardado = await self._consents.add(
            Consent.request(
                template,
                appointment_id=cita.id,
                pet_id=cita.pet_id,
                client_id=cita.client_id,
                requested_by=command.requester.user_id,
                details=details,
                now=momento,
            )
        )
        await self._activity.record(
            command.requester.user_id,
            ActivityKind.CONSENT_REQUESTED,
            f"{guardado.kind.label}, cita {cita.id}",
        )
        return guardado
