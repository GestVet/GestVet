from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.consents.adapters.persistence.models import ConsentRow, ConsentTemplateRow
from gestvet.modules.consents.domain.entities import (
    Consent,
    ConsentChannel,
    ConsentKind,
    ConsentStatus,
    ConsentTemplate,
)


def template_row_to_entity(row: ConsentTemplateRow) -> ConsentTemplate:
    return ConsentTemplate(
        id=row.id,
        kind=ConsentKind(row.kind),
        version=row.version,
        title=row.title,
        body=row.body,
        is_active=row.is_active,
        created_at=as_utc(row.created_at),
    )


def row_to_entity(row: ConsentRow) -> Consent:
    return Consent(
        id=row.id,
        template_id=row.template_id,
        kind=ConsentKind(row.kind),
        pet_id=row.pet_id,
        client_id=row.client_id,
        appointment_id=row.appointment_id,
        status=ConsentStatus(row.status),
        channel=ConsentChannel(row.channel) if row.channel else None,
        text_snapshot=row.text_snapshot,
        text_sha256=row.text_sha256,
        signer_name=row.signer_name,
        signer_user_id=row.signer_user_id,
        witness_id=row.witness_id,
        requested_by=row.requested_by,
        details=row.details,
        decision_reason=row.decision_reason,
        ip=row.ip,
        user_agent=row.user_agent,
        decided_at=as_utc(row.decided_at) if row.decided_at else None,
        created_at=as_utc(row.created_at),
    )


def entity_to_row(consent: Consent) -> ConsentRow:
    return ConsentRow(
        template_id=consent.template_id,
        kind=consent.kind.value,
        pet_id=consent.pet_id,
        client_id=consent.client_id,
        appointment_id=consent.appointment_id,
        text_snapshot=consent.text_snapshot,
        text_sha256=consent.text_sha256,
        requested_by=consent.requested_by,
        details=consent.details,
        created_at=consent.created_at,
        **decision_columns(consent),
    )


def decision_columns(consent: Consent) -> dict[str, object]:
    """Lo único que cambia al responder un pedido. El texto y su huella, nunca."""
    return {
        "status": consent.status.value,
        "channel": consent.channel.value if consent.channel else None,
        "signer_name": consent.signer_name,
        "signer_user_id": consent.signer_user_id,
        "witness_id": consent.witness_id,
        "decision_reason": consent.decision_reason,
        "ip": consent.ip,
        "user_agent": consent.user_agent,
        "decided_at": consent.decided_at,
    }
