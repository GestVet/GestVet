"""Bitácora de lo que hace cada cuenta.

Vive en el núcleo y no en un módulo de dominio porque la escriben todos: las
citas, las mascotas, la agenda y las propias cuentas. Si la poseyera uno de
ellos, el resto tendría que importarlo y dejarían de ser independientes.

Este archivo es Python puro a propósito: lo importan los casos de uso, que son
los que deciden qué se registra. El adaptador que escribe en la base vive en
`activity_log.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page

MAX_DETAIL_LENGTH = 200


class ActivityKind(StrEnum):
    """Qué ocurrió.

    El original guardaba una frase armada a mano, del estilo "Reservó cita de
    tipo Consulta general". Eso impide filtrar y contar: cada variante del
    texto es un valor distinto. Acá el tipo es un código estable y la frase
    legible se arma al mostrarla, así que cambiar la redacción no rompe el
    historial.
    """

    SIGNED_IN = "signed_in"
    CLIENT_REGISTERED = "client_registered"
    PROFILE_UPDATED = "profile_updated"
    STAFF_REGISTERED = "staff_registered"
    STAFF_SPECIALTIES_UPDATED = "staff_specialties_updated"
    USER_STATUS_CHANGED = "user_status_changed"
    GUARD_DUTY_TOGGLED = "guard_duty_toggled"
    PET_REGISTERED = "pet_registered"
    PET_STATUS_CHANGED = "pet_status_changed"
    PET_STATUS_CORRECTED = "pet_status_corrected"
    PET_PROFILE_UPDATED = "pet_profile_updated"
    PET_CLINICAL_PROFILE_UPDATED = "pet_clinical_profile_updated"
    SLOT_PUBLISHED = "slot_published"
    SLOT_WITHDRAWN = "slot_withdrawn"
    SHIFT_ASSIGNED = "shift_assigned"
    SHIFT_REMOVED = "shift_removed"
    WEEKLY_PLAN_APPLIED = "weekly_plan_applied"
    SHIFT_CHANGE_REQUESTED = "shift_change_requested"
    SHIFT_CHANGE_RESOLVED = "shift_change_resolved"
    APPOINTMENT_BOOKED = "appointment_booked"
    EMERGENCY_OPENED = "emergency_opened"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_COMPLETED = "appointment_completed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_NO_SHOW = "appointment_no_show"
    CLINICAL_ENTRY_ADDED = "clinical_entry_added"
    ATTACHMENT_UPLOADED = "attachment_uploaded"
    ATTACHMENT_DELETED = "attachment_deleted"
    PAYMENT_REGISTERED = "payment_registered"
    PAYMENT_VOIDED = "payment_voided"
    REVIEW_SUBMITTED = "review_submitted"
    COMPLAINT_FILED = "complaint_filed"
    CONSENT_ACCEPTED = "consent_accepted"
    CONSENT_REQUESTED = "consent_requested"
    CONSENT_DECLINED = "consent_declined"
    CONSENT_WAIVED = "consent_waived"
    HOSPITALIZATION_OPENED = "hospitalization_opened"
    HOSPITALIZATION_NOTE_ADDED = "hospitalization_note_added"
    HOSPITALIZATION_DISCHARGED = "hospitalization_discharged"
    ACCESS_ROLE_CREATED = "access_role_created"
    ACCESS_ROLE_UPDATED = "access_role_updated"
    ACCESS_ROLE_DELETED = "access_role_deleted"
    ACCESS_ROLE_ASSIGNED = "access_role_assigned"
    DOCUMENT_LOOKED_UP = "document_looked_up"

    @property
    def label(self) -> str:
        return _KIND_LABELS[self]


_KIND_LABELS: dict[ActivityKind, str] = {
    ActivityKind.DOCUMENT_LOOKED_UP: "Consultó un DNI",
    ActivityKind.SIGNED_IN: "Inició sesión",
    ActivityKind.CLIENT_REGISTERED: "Se registró como cliente",
    ActivityKind.PROFILE_UPDATED: "Actualizó su perfil",
    ActivityKind.STAFF_REGISTERED: "Dio de alta a un veterinario",
    ActivityKind.STAFF_SPECIALTIES_UPDATED: "Actualizó las especialidades de un veterinario",
    ActivityKind.USER_STATUS_CHANGED: "Cambió el estado de una cuenta",
    ActivityKind.GUARD_DUTY_TOGGLED: "Cambió el turno de guardia",
    ActivityKind.PET_REGISTERED: "Registró una mascota",
    ActivityKind.PET_STATUS_CHANGED: "Cambió el estado de una mascota",
    ActivityKind.PET_STATUS_CORRECTED: "Corrigió el estado de una mascota",
    ActivityKind.PET_PROFILE_UPDATED: "Actualizó el perfil de una mascota",
    ActivityKind.PET_CLINICAL_PROFILE_UPDATED: "Actualizó los datos clínicos de una mascota",
    ActivityKind.SLOT_PUBLISHED: "Publicó un tramo de disponibilidad",
    ActivityKind.SLOT_WITHDRAWN: "Retiró un tramo de disponibilidad",
    ActivityKind.SHIFT_ASSIGNED: "Asignó un turno",
    ActivityKind.SHIFT_REMOVED: "Quitó un turno",
    ActivityKind.WEEKLY_PLAN_APPLIED: "Aplicó un horario semanal",
    ActivityKind.SHIFT_CHANGE_REQUESTED: "Pidió un cambio de turno",
    ActivityKind.SHIFT_CHANGE_RESOLVED: "Respondió un pedido de cambio de turno",
    ActivityKind.APPOINTMENT_BOOKED: "Reservó una cita",
    ActivityKind.EMERGENCY_OPENED: "Abrió una emergencia",
    ActivityKind.APPOINTMENT_CONFIRMED: "Confirmó una cita",
    ActivityKind.APPOINTMENT_COMPLETED: "Completó una cita",
    ActivityKind.APPOINTMENT_CANCELLED: "Canceló una cita",
    ActivityKind.APPOINTMENT_NO_SHOW: "Marcó una cita como no asistida",
    ActivityKind.CLINICAL_ENTRY_ADDED: "Agregó una entrada a la historia clínica",
    ActivityKind.ATTACHMENT_UPLOADED: "Adjuntó un archivo a la historia clínica",
    ActivityKind.ATTACHMENT_DELETED: "Quitó un adjunto de la historia clínica",
    ActivityKind.PAYMENT_REGISTERED: "Registró un pago",
    ActivityKind.PAYMENT_VOIDED: "Anuló un pago",
    ActivityKind.REVIEW_SUBMITTED: "Dejó una reseña",
    ActivityKind.COMPLAINT_FILED: "Presentó un reclamo",
    ActivityKind.CONSENT_ACCEPTED: "Registró un consentimiento informado",
    ActivityKind.CONSENT_REQUESTED: "Pidió un consentimiento informado",
    ActivityKind.CONSENT_DECLINED: "Rechazó un consentimiento informado",
    ActivityKind.CONSENT_WAIVED: "Atendió sin consentimiento por urgencia vital",
    ActivityKind.HOSPITALIZATION_OPENED: "Abrió una internación",
    ActivityKind.HOSPITALIZATION_NOTE_ADDED: "Agregó una nota de seguimiento",
    ActivityKind.HOSPITALIZATION_DISCHARGED: "Dio de alta una internación",
    ActivityKind.ACCESS_ROLE_CREATED: "Creó un rol",
    ActivityKind.ACCESS_ROLE_UPDATED: "Cambió los permisos de un rol",
    ActivityKind.ACCESS_ROLE_DELETED: "Borró un rol",
    ActivityKind.ACCESS_ROLE_ASSIGNED: "Cambió el rol de una cuenta",
}


@dataclass(frozen=True, slots=True)
class ActivityRecord:
    user_id: int
    kind: ActivityKind
    detail: str = ""
    id: int | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", self.detail.strip()[:MAX_DETAIL_LENGTH])


@dataclass(frozen=True, slots=True)
class ActivityQuery:
    user_ids: frozenset[int] | None = None
    kinds: frozenset[ActivityKind] | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


class ActivityRecorder(Protocol):
    """Escribe en la bitácora.

    Lo usan los casos de uso, que son los que saben qué ocurrió. Registrar es
    parte de la transacción: si la operación se deshace, el asiento también.
    """

    async def record(self, user_id: int, kind: ActivityKind, detail: str = "") -> None: ...


class ActivityReader(Protocol):
    async def search(self, query: ActivityQuery) -> Page[ActivityRecord]: ...
