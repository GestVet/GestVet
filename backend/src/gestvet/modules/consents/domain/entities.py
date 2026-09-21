"""Entidades de dominio de consentimientos informados.

Python puro. La mascota, el cliente y el personal se referencian por
identificador: cada uno vive en otro módulo y este no puede importarlos.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from gestvet.modules.consents.domain.details import ConsentDetails
from gestvet.modules.consents.domain.exceptions import (
    ConsentExpired,
    ConsentNotPending,
    InvalidConsent,
    InvalidSignerName,
    InvalidWaiver,
)

MAX_SIGNER_NAME_LENGTH = 120
MIN_SIGNER_NAME_WORDS = 2
MAX_USER_AGENT_LENGTH = 300
MAX_IP_LENGTH = 45
MIN_JUSTIFICATION_LENGTH = 20
MAX_JUSTIFICATION_LENGTH = 1000
MAX_DECLINE_REASON_LENGTH = 500

# Cuánto espera un pedido la respuesta del dueño. Pasado ese plazo la
# situación clínica pudo cambiar, y lo que se firmara ya no describiría lo
# que el veterinario propuso: hay que volver a pedirlo.
PENDING_VALIDITY = timedelta(hours=24)


class ConsentKind(StrEnum):
    """Para qué se pide el consentimiento.

    Cada tipo tiene su propia línea de versiones del texto. Sumar uno es
    agregar el valor acá y sembrar su primera versión en una migración: las
    tablas guardan el tipo como texto y no cambian.
    """

    EMERGENCY_RISK = "emergency_risk"
    HIGH_RISK = "high_risk"
    PROCEDURE = "procedure"
    ANESTHESIA = "anesthesia"
    HOSPITALIZATION = "hospitalization"
    EUTHANASIA = "euthanasia"

    @property
    def label(self) -> str:
        return _KIND_LABELS[self]

    @property
    def requestable(self) -> bool:
        """Si lo pide el veterinario desde una cita.

        El riesgo de emergencia no: lo firma el dueño al abrirla, antes de que
        exista la cita.
        """
        return self is not ConsentKind.EMERGENCY_RISK

    @property
    def requires_procedure(self) -> bool:
        """Si el detalle tiene que nombrar el procedimiento.

        Nadie autoriza "una cirugía" en abstracto: sin saber cuál, la firma no
        dice qué se aceptó.
        """
        return self in _KINDS_WITH_PROCEDURE


_KIND_LABELS: dict[ConsentKind, str] = {
    ConsentKind.EMERGENCY_RISK: "Riesgo de la atención de emergencia",
    ConsentKind.HIGH_RISK: "Pronóstico reservado y riesgo alto",
    ConsentKind.PROCEDURE: "Cirugía o procedimiento invasivo",
    ConsentKind.ANESTHESIA: "Anestesia o sedación",
    ConsentKind.HOSPITALIZATION: "Internación",
    ConsentKind.EUTHANASIA: "Eutanasia",
}

_KINDS_WITH_PROCEDURE = frozenset(
    {ConsentKind.PROCEDURE, ConsentKind.ANESTHESIA, ConsentKind.EUTHANASIA}
)


class ConsentStatus(StrEnum):
    """Estado de un consentimiento.

    `expired` no se guarda nunca: un pedido pendiente vence solo, y el estado
    se calcula al leerlo (ver `Consent.effective_status`).
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    WAIVED_EMERGENCY = "waived_emergency"

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]


_STATUS_LABELS: dict[ConsentStatus, str] = {
    ConsentStatus.PENDING: "Pendiente",
    ConsentStatus.ACCEPTED: "Aceptado",
    ConsentStatus.DECLINED: "Rechazado",
    ConsentStatus.EXPIRED: "Vencido",
    ConsentStatus.WAIVED_EMERGENCY: "Sin consentimiento por urgencia vital",
}


class ConsentChannel(StrEnum):
    ONLINE = "online"
    IN_PERSON = "in_person"

    @property
    def label(self) -> str:
        return _CHANNEL_LABELS[self]


_CHANNEL_LABELS: dict[ConsentChannel, str] = {
    ConsentChannel.ONLINE: "En línea",
    ConsentChannel.IN_PERSON: "Presencial",
}


def normalize_signer_name(raw: str) -> str:
    """El nombre completo de quien firma, tal como queda en el registro.

    Dos palabras como mínimo: un nombre de pila solo no identifica a nadie, y
    la firma escrita vale lo que vale el nombre. Los espacios de más se
    colapsan para que el mismo nombre no quede guardado de dos formas.
    """
    cleaned = " ".join(raw.split())
    if len(cleaned) > MAX_SIGNER_NAME_LENGTH:
        raise InvalidSignerName(
            f"El nombre de quien firma admite {MAX_SIGNER_NAME_LENGTH} caracteres como máximo."
        )
    if len(cleaned.split()) < MIN_SIGNER_NAME_WORDS:
        raise InvalidSignerName("Escribí el nombre completo de quien firma: nombre y apellido.")
    return cleaned


def normalize_justification(raw: str) -> str:
    """Por qué se atendió sin consentimiento, tal como queda en el registro.

    Es la única defensa de esa decisión ante el dueño o ante un reclamo: un
    "urgente" suelto no alcanza, tiene que decir qué pasaba y por qué no se
    pudo esperar.
    """
    cleaned = raw.strip()
    if len(cleaned) < MIN_JUSTIFICATION_LENGTH:
        raise InvalidWaiver(
            "Explicá por qué no se pudo pedir el consentimiento: qué le pasaba a la mascota "
            f"y por qué no se ubicó al responsable (al menos {MIN_JUSTIFICATION_LENGTH} "
            "caracteres)."
        )
    if len(cleaned) > MAX_JUSTIFICATION_LENGTH:
        raise InvalidWaiver(
            f"La justificación admite {MAX_JUSTIFICATION_LENGTH} caracteres como máximo."
        )
    return cleaned


def normalize_decline_reason(raw: str | None) -> str | None:
    cleaned = (raw or "").strip()
    if len(cleaned) > MAX_DECLINE_REASON_LENGTH:
        raise InvalidConsent(
            f"El motivo del rechazo admite {MAX_DECLINE_REASON_LENGTH} caracteres como máximo."
        )
    return cleaned or None


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class ConsentTemplate:
    """Un texto de consentimiento en una versión puntual.

    No se edita nunca: un consentimiento firmado apunta a la versión que se
    leyó, y cambiarla en el lugar reescribiría lo que otra persona aceptó.
    Corregir el texto es publicar una versión nueva y desactivar la anterior.
    """

    kind: ConsentKind
    version: int
    title: str
    body: str
    is_active: bool = True
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def render(self, details: ConsentDetails | None = None) -> str:
        """El texto exacto que se muestra y que queda copiado en cada firma."""
        text = f"{self.title}\n\n{self.body}"
        return details.render_below(text) if details is not None else text


@dataclass(slots=True)
class Consent:
    """La aceptación (o no) de un texto concreto, por una persona concreta.

    `text_snapshot` y `text_sha256` hacen que el registro se sostenga solo:
    aunque la plantilla cambiara o se borrara, queda lo que se leyó y una
    huella para demostrar que no se tocó después.

    Un pedido del veterinario nace `pending`, sin canal ni firma: los dos
    dependen de cómo responda el dueño. `decision_reason` guarda el motivo de
    un rechazo o la justificación de una atención sin consentimiento; no va en
    `details` porque no es parte del texto que el dueño leyó.
    """

    template_id: int
    kind: ConsentKind
    pet_id: int
    client_id: int
    status: ConsentStatus
    channel: ConsentChannel | None
    text_snapshot: str
    text_sha256: str
    signer_name: str | None
    decided_at: datetime | None
    appointment_id: int | None = None
    signer_user_id: int | None = None
    witness_id: int | None = None
    requested_by: int | None = None
    details: dict[str, object] | None = None
    decision_reason: str | None = None
    ip: str = ""
    user_agent: str = ""
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.text_sha256 != fingerprint(self.text_snapshot):
            raise InvalidConsent("La huella no corresponde al texto firmado.")
        self.ip = self.ip[:MAX_IP_LENGTH]
        self.user_agent = self.user_agent[:MAX_USER_AGENT_LENGTH]
        self._validate()

    def _validate(self) -> None:
        if self.decided_at is not None:
            if self.decided_at.tzinfo is None:
                raise InvalidConsent("La fecha de la firma debe traer zona horaria.")
            self.decided_at = self.decided_at.astimezone(UTC)
        if self.signer_name is not None:
            self.signer_name = normalize_signer_name(self.signer_name)
        if self.channel is ConsentChannel.IN_PERSON and self.witness_id is None:
            raise InvalidConsent("Un consentimiento presencial necesita al personal que lo tomó.")
        _RULES_BY_STATUS.get(self.status, _no_rule)(self)

    @classmethod
    def accept(
        cls,
        template: ConsentTemplate,
        *,
        pet_id: int,
        client_id: int,
        channel: ConsentChannel,
        signer_name: str,
        signer_user_id: int | None = None,
        witness_id: int | None = None,
        requested_by: int | None = None,
        details: dict[str, object] | None = None,
        ip: str = "",
        user_agent: str = "",
        now: datetime | None = None,
    ) -> Consent:
        if template.id is None:
            raise InvalidConsent("La plantilla debe estar guardada antes de firmarla.")
        texto = template.render()
        return cls(
            template_id=template.id,
            kind=template.kind,
            pet_id=pet_id,
            client_id=client_id,
            status=ConsentStatus.ACCEPTED,
            channel=channel,
            text_snapshot=texto,
            text_sha256=fingerprint(texto),
            signer_name=signer_name,
            decided_at=now or datetime.now(UTC),
            signer_user_id=signer_user_id,
            witness_id=witness_id,
            requested_by=requested_by,
            details=details,
            ip=ip,
            user_agent=user_agent,
        )

    @classmethod
    def request(
        cls,
        template: ConsentTemplate,
        *,
        appointment_id: int,
        pet_id: int,
        client_id: int,
        requested_by: int,
        details: ConsentDetails,
        now: datetime | None = None,
    ) -> Consent:
        """El pedido del veterinario, con el texto ya armado tal como lo va a leer el dueño."""
        if template.id is None:
            raise InvalidConsent("La plantilla debe estar guardada antes de pedirla.")
        texto = template.render(details)
        return cls(
            template_id=template.id,
            kind=template.kind,
            pet_id=pet_id,
            client_id=client_id,
            status=ConsentStatus.PENDING,
            channel=None,
            text_snapshot=texto,
            text_sha256=fingerprint(texto),
            signer_name=None,
            decided_at=None,
            appointment_id=appointment_id,
            requested_by=requested_by,
            details=details.to_json(),
            created_at=now or datetime.now(UTC),
        )

    @classmethod
    def waive(
        cls,
        template: ConsentTemplate,
        *,
        appointment_id: int,
        pet_id: int,
        client_id: int,
        recorded_by: int,
        justification: str,
        now: datetime | None = None,
    ) -> Consent:
        """Constancia de que se atendió sin consentimiento porque no había cómo pedirlo.

        Copia igual el texto vigente: queda cuál era el consentimiento que no
        se pudo pedir, en qué versión.
        """
        if template.id is None:
            raise InvalidConsent("La plantilla debe estar guardada.")
        momento = now or datetime.now(UTC)
        texto = template.render()
        return cls(
            template_id=template.id,
            kind=template.kind,
            pet_id=pet_id,
            client_id=client_id,
            status=ConsentStatus.WAIVED_EMERGENCY,
            channel=None,
            text_snapshot=texto,
            text_sha256=fingerprint(texto),
            signer_name=None,
            decided_at=momento,
            appointment_id=appointment_id,
            requested_by=recorded_by,
            decision_reason=justification,
            created_at=momento,
        )

    @property
    def expires_at(self) -> datetime | None:
        if self.status is not ConsentStatus.PENDING:
            return None
        return self.created_at + PENDING_VALIDITY

    def effective_status(self, now: datetime | None = None) -> ConsentStatus:
        """El estado en este instante: un pedido sin respuesta vence solo.

        Se calcula al leer, igual que la inasistencia de una cita, en vez de
        necesitar un proceso en segundo plano que lo marque.
        """
        expira = self.expires_at
        if expira is not None and (now or datetime.now(UTC)) >= expira:
            return ConsentStatus.EXPIRED
        return self.status

    def accept_request(
        self,
        *,
        signer_name: str,
        channel: ConsentChannel,
        signer_user_id: int | None = None,
        witness_id: int | None = None,
        ip: str = "",
        user_agent: str = "",
        now: datetime | None = None,
    ) -> None:
        momento = now or datetime.now(UTC)
        self._ensure_answerable(momento)
        self.status = ConsentStatus.ACCEPTED
        self.channel = channel
        self.signer_name = signer_name
        self.signer_user_id = signer_user_id
        self.witness_id = witness_id
        self.decided_at = momento
        self.ip = ip[:MAX_IP_LENGTH]
        self.user_agent = user_agent[:MAX_USER_AGENT_LENGTH]
        self._validate()

    def decline(
        self,
        *,
        reason: str | None,
        signer_user_id: int,
        ip: str = "",
        user_agent: str = "",
        now: datetime | None = None,
    ) -> None:
        momento = now or datetime.now(UTC)
        self._ensure_answerable(momento)
        self.decision_reason = normalize_decline_reason(reason)
        self.status = ConsentStatus.DECLINED
        self.channel = ConsentChannel.ONLINE
        self.signer_user_id = signer_user_id
        self.decided_at = momento
        self.ip = ip[:MAX_IP_LENGTH]
        self.user_agent = user_agent[:MAX_USER_AGENT_LENGTH]
        self._validate()

    def _ensure_answerable(self, now: datetime) -> None:
        estado = self.effective_status(now)
        if estado is ConsentStatus.EXPIRED:
            raise ConsentExpired()
        if estado is not ConsentStatus.PENDING:
            raise ConsentNotPending(estado.label)

    def visible_to(self, user_id: int, is_staff: bool) -> bool:
        return is_staff or self.client_id == user_id


def _check_accepted(consent: Consent) -> None:
    if consent.signer_name is None or consent.channel is None or consent.decided_at is None:
        raise InvalidConsent("Un consentimiento aceptado necesita firma, canal y fecha.")


def _check_declined(consent: Consent) -> None:
    if consent.channel is None or consent.decided_at is None:
        raise InvalidConsent("Un rechazo necesita canal y fecha.")


def _check_pending(consent: Consent) -> None:
    if consent.appointment_id is None or consent.requested_by is None:
        raise InvalidConsent("Un pedido de consentimiento necesita la cita y quién lo pidió.")
    if consent.decided_at is not None or consent.signer_name is not None:
        raise InvalidConsent("Un pedido pendiente todavía no tiene firma.")


def _check_waived(consent: Consent) -> None:
    if consent.appointment_id is None or consent.requested_by is None:
        raise InvalidConsent("La atención sin consentimiento necesita la cita y quién la registró.")
    if consent.decided_at is None:
        raise InvalidConsent("La atención sin consentimiento necesita la fecha.")
    consent.decision_reason = normalize_justification(consent.decision_reason or "")


def _no_rule(_consent: Consent) -> None:
    return None


_RULES_BY_STATUS = {
    ConsentStatus.ACCEPTED: _check_accepted,
    ConsentStatus.DECLINED: _check_declined,
    ConsentStatus.PENDING: _check_pending,
    ConsentStatus.WAIVED_EMERGENCY: _check_waived,
}
