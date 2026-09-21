"""Contrato HTTP del módulo de consentimientos.

La dirección IP y el navegador de quien firma se guardan como constancia pero
no salen en ninguna respuesta: son datos personales que la pantalla no usa.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from gestvet.modules.consents.domain.details import (
    MAX_NOTES_LENGTH,
    MAX_PROCEDURE_LENGTH,
    MAX_PROGNOSIS_LENGTH,
    ConsentDetails,
)
from gestvet.modules.consents.domain.entities import (
    MAX_DECLINE_REASON_LENGTH,
    MAX_JUSTIFICATION_LENGTH,
    MAX_SIGNER_NAME_LENGTH,
    Consent,
    ConsentChannel,
    ConsentKind,
    ConsentStatus,
    ConsentTemplate,
)


class AcceptEmergencyRiskRequest(BaseModel):
    pet_id: int = Field(ge=1)
    template_id: int = Field(ge=1)
    signer_name: str = Field(min_length=1, max_length=MAX_SIGNER_NAME_LENGTH)
    # La casilla marcada. Sin ella no hay consentimiento, así que ni se admite `false`.
    accepted: Literal[True]


class RecordInPersonEmergencyRiskRequest(AcceptEmergencyRiskRequest):
    """Acá sí viaja `client_id`: firma el responsable, no la cuenta que lo registra."""

    client_id: int = Field(ge=1)


class ConsentTemplateResponse(BaseModel):
    id: int
    kind: ConsentKind
    kind_label: str
    version: int
    title: str
    body: str
    # El texto exacto que queda copiado en la firma: título y cuerpo juntos.
    text: str

    @classmethod
    def from_entity(cls, template: ConsentTemplate) -> ConsentTemplateResponse:
        return cls(
            id=template.id or 0,
            kind=template.kind,
            kind_label=template.kind.label,
            version=template.version,
            title=template.title,
            body=template.body,
            text=template.render(),
        )


class ConsentDetailsPayload(BaseModel):
    """Lo que el veterinario agrega al texto. Qué es obligatorio lo decide el dominio por tipo."""

    procedure: str | None = Field(default=None, max_length=MAX_PROCEDURE_LENGTH)
    prognosis: str | None = Field(default=None, max_length=MAX_PROGNOSIS_LENGTH)
    # En soles.
    estimated_cost: Decimal | None = Field(default=None, gt=0, max_digits=9, decimal_places=2)
    notes: str | None = Field(default=None, max_length=MAX_NOTES_LENGTH)

    @classmethod
    def from_entity(cls, details: ConsentDetails) -> ConsentDetailsPayload:
        return cls(
            procedure=details.procedure or None,
            prognosis=details.prognosis or None,
            estimated_cost=details.estimated_cost,
            notes=details.notes or None,
        )


class RequestConsentRequest(BaseModel):
    appointment_id: int = Field(ge=1)
    kind: ConsentKind
    details: ConsentDetailsPayload = Field(default_factory=ConsentDetailsPayload)


class AcceptConsentRequest(BaseModel):
    signer_name: str = Field(min_length=1, max_length=MAX_SIGNER_NAME_LENGTH)
    # La casilla marcada. Sin ella no hay consentimiento, así que ni se admite `false`.
    accepted: Literal[True]


class DeclineConsentRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=MAX_DECLINE_REASON_LENGTH)


class WaiveConsentRequest(BaseModel):
    appointment_id: int = Field(ge=1)
    kind: ConsentKind
    # El mínimo lo aplica el dominio, con un mensaje que explica qué escribir.
    justification: str = Field(min_length=1, max_length=MAX_JUSTIFICATION_LENGTH)


class ConsentResponse(BaseModel):
    id: int
    template_id: int
    kind: ConsentKind
    kind_label: str
    appointment_id: int | None
    pet_id: int
    pet_name: str | None
    client_id: int
    # El estado efectivo: un pedido sin respuesta pasado su plazo sale vencido.
    status: ConsentStatus
    status_label: str
    channel: ConsentChannel | None
    channel_label: str | None
    text_snapshot: str
    text_sha256: str
    signer_name: str | None
    signer_user_id: int | None
    witness_id: int | None
    witness_name: str | None
    requested_by: int | None
    requested_by_name: str | None
    details: ConsentDetailsPayload | None
    # Motivo de un rechazo o justificación de una atención sin consentimiento.
    decision_reason: str | None
    decided_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    @classmethod
    def from_entity(
        cls,
        consent: Consent,
        pet_names: dict[int, str] | None = None,
        user_names: dict[int, str] | None = None,
    ) -> ConsentResponse:
        mascotas = pet_names or {}
        personas = user_names or {}
        estado = consent.effective_status()
        return cls(
            id=consent.id or 0,
            template_id=consent.template_id,
            kind=consent.kind,
            kind_label=consent.kind.label,
            appointment_id=consent.appointment_id,
            pet_id=consent.pet_id,
            pet_name=mascotas.get(consent.pet_id),
            client_id=consent.client_id,
            status=estado,
            status_label=estado.label,
            channel=consent.channel,
            channel_label=consent.channel.label if consent.channel else None,
            text_snapshot=consent.text_snapshot,
            text_sha256=consent.text_sha256,
            signer_name=consent.signer_name,
            signer_user_id=consent.signer_user_id,
            witness_id=consent.witness_id,
            witness_name=personas.get(consent.witness_id or 0),
            requested_by=consent.requested_by,
            requested_by_name=personas.get(consent.requested_by or 0),
            details=(
                ConsentDetailsPayload.from_entity(ConsentDetails.from_json(consent.details))
                if consent.details
                else None
            ),
            decision_reason=consent.decision_reason,
            decided_at=consent.decided_at,
            expires_at=consent.expires_at,
            created_at=consent.created_at,
        )


class ConsentListResponse(BaseModel):
    items: list[ConsentResponse]
    # Solo al listar los de una cita como personal: si ahí se admite atender
    # sin consentimiento por urgencia vital.
    appointment_is_emergency: bool | None = None
