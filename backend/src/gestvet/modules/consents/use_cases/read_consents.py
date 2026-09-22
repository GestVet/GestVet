"""Casos de uso de lectura: el texto vigente, un consentimiento y los de una cita o un cliente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from gestvet.core.identity import Principal, Role
from gestvet.modules.consents.domain.entities import (
    Consent,
    ConsentKind,
    ConsentStatus,
    ConsentTemplate,
)
from gestvet.modules.consents.domain.exceptions import (
    AppointmentRequired,
    ConsentNotFound,
    TemplateNotFound,
)
from gestvet.modules.consents.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.consents.ports.consent_repository import (
    ConsentRepository,
    ConsentTemplateRepository,
)
from gestvet.modules.consents.use_cases.appointment_access import appointment_for


class GetCurrentTemplate:
    def __init__(self, templates: ConsentTemplateRepository) -> None:
        self._templates = templates

    async def __call__(self, kind: ConsentKind) -> ConsentTemplate:
        template = await self._templates.current(kind)
        if template is None:
            raise TemplateNotFound()
        return template


class GetConsent:
    """El dueño ve los suyos y el personal cualquiera.

    Uno ajeno responde igual que uno inexistente, para no confirmar que el
    identificador es de alguien.
    """

    def __init__(self, consents: ConsentRepository) -> None:
        self._consents = consents

    async def __call__(self, consent_id: int, principal: Principal) -> Consent:
        consent = await self._consents.get(consent_id)
        if consent is None or not consent.visible_to(
            principal.user_id, is_staff=principal.role is not Role.CLIENT
        ):
            raise ConsentNotFound(consent_id)
        return consent


@dataclass(frozen=True, slots=True)
class ConsentQuery:
    appointment_id: int | None = None
    status: ConsentStatus | None = None


@dataclass(frozen=True, slots=True)
class ConsentListing:
    items: list[Consent]
    # Solo cuando el personal pide los de una cita: dice si ahí se admite
    # atender sin consentimiento por urgencia vital. `appointments` no lo
    # expone en la cita, y esta lectura ya tiene la respuesta a mano.
    appointment_is_emergency: bool | None = None


class ListConsents:
    """Los consentimientos que quien pregunta puede ver.

    El cliente ve los pedidos que le hicieron, de todas sus mascotas. El
    personal, los de una cita que atiende: sin cita no hay listado, porque el
    padrón entero de firmas no es algo que un veterinario necesite recorrer.

    El filtro por estado usa el estado efectivo: pedir los pendientes no trae
    los que vencieron sin respuesta.
    """

    def __init__(self, consents: ConsentRepository, appointments: AppointmentDirectory) -> None:
        self._consents = consents
        self._appointments = appointments

    async def __call__(
        self, query: ConsentQuery, principal: Principal, now: datetime | None = None
    ) -> ConsentListing:
        momento = now or datetime.now(UTC)
        es_emergencia: bool | None = None
        if principal.role is Role.CLIENT:
            items = [
                consent
                for consent in await self._consents.list_for_client(principal.user_id)
                if query.appointment_id in (None, consent.appointment_id)
            ]
        elif query.appointment_id is None:
            raise AppointmentRequired()
        else:
            cita = await appointment_for(self._appointments, query.appointment_id, principal)
            es_emergencia = cita.is_emergency
            items = await self._consents.list_for_appointment(query.appointment_id)
        if query.status is not None:
            items = [item for item in items if item.effective_status(momento) is query.status]
        return ConsentListing(items, es_emergencia)
