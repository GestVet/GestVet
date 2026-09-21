"""Lo que comparten los dos routers de consentimientos: errores, respuestas y avisos."""

from __future__ import annotations

from fastapi import HTTPException, status

from gestvet.core.realtime import CONSENTS_TOPIC, EventPublisher, RealtimeEvent
from gestvet.modules.consents.adapters.api.schemas import ConsentResponse
from gestvet.modules.consents.domain.entities import Consent
from gestvet.modules.consents.domain.exceptions import (
    AppointmentCancelled,
    AppointmentNotFound,
    AppointmentRequired,
    ConsentExpired,
    ConsentNotFound,
    ConsentNotPending,
    ConsentsError,
    InvalidConsent,
    InvalidConsentDetails,
    InvalidSignerName,
    InvalidWaiver,
    KindNotRequestable,
    PendingRequestExists,
    PetNotOwned,
    TemplateNotFound,
    TemplateOutdated,
    WaiverOnlyForEmergencies,
)
from gestvet.modules.consents.ports.name_directory import NameDirectory

_NOT_FOUND = (PetNotOwned, TemplateNotFound, ConsentNotFound, AppointmentNotFound)
_CONFLICT = (
    TemplateOutdated,
    ConsentNotPending,
    ConsentExpired,
    PendingRequestExists,
    AppointmentCancelled,
    WaiverOnlyForEmergencies,
)
_UNPROCESSABLE = (
    InvalidSignerName,
    InvalidConsent,
    InvalidConsentDetails,
    InvalidWaiver,
    KindNotRequestable,
    AppointmentRequired,
)


def http_error(error: ConsentsError) -> HTTPException:
    if isinstance(error, _NOT_FOUND):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(error))
    if isinstance(error, _CONFLICT):
        return HTTPException(status.HTTP_409_CONFLICT, str(error))
    if isinstance(error, _UNPROCESSABLE):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error))
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(error))


async def responses_for(consents: list[Consent], names: NameDirectory) -> list[ConsentResponse]:
    """Con el nombre de la mascota y del personal: el dueño tiene que ver qué firma y para quién."""
    mascotas = await names.pet_names(consent.pet_id for consent in consents)
    personas = await names.user_names(
        user_id
        for consent in consents
        for user_id in (consent.requested_by, consent.witness_id)
        if user_id is not None
    )
    return [ConsentResponse.from_entity(consent, mascotas, personas) for consent in consents]


async def response_for(consent: Consent, names: NameDirectory) -> ConsentResponse:
    return (await responses_for([consent], names))[0]


def notify(events: EventPublisher, consent: Consent) -> None:
    """Avisa al dueño y al personal que participó; el aviso no lleva datos."""
    destinatarios = {
        user_id
        for user_id in (consent.client_id, consent.requested_by, consent.witness_id)
        if user_id is not None
    }
    events.publish(
        RealtimeEvent(
            topic=CONSENTS_TOPIC,
            user_ids=frozenset(destinatarios),
            reference_id=consent.id,
        )
    )
