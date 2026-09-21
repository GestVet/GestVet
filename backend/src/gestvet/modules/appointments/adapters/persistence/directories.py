"""Lectores hacia datos que posee otro módulo.

Una cita necesita dos cosas que no son suyas: saber si la mascota es del
cliente y si el veterinario tiene turno a esa hora. `pets` y `availability` son
módulos de dominio independientes y este no puede importarlos.

La salida es la misma que usa `gestvet.core.auth` para la identidad: una
proyección de solo lectura, escrita a mano contra la tabla del otro módulo y
declarada como puerto para que el negocio no sepa de dónde sale la respuesta.
El acoplamiento es al nombre de la tabla, está acotado a estas consultas y lo
cubren las pruebas.

La regla es estricta: se lee, nunca se escribe. Modificar una mascota o un
turno sigue siendo competencia exclusiva de su módulo.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, bindparam, column, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.appointments.ports.appointment_labels import AppointmentLabels
from gestvet.modules.appointments.ports.client_directory import ClientContact
from gestvet.modules.appointments.ports.repositories import ScheduleSlot


def _as_utc(moment: datetime) -> datetime:
    # SQLite devuelve la fecha sin zona aunque se haya guardado en UTC.
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


# Una consulta escrita a mano no pasa por el sistema de tipos de SQLAlchemy,
# así que un `datetime` llegaría crudo al driver: en SQLite eso cae en el
# adaptador obsoleto que Python marcó para borrar. Declarar el tipo del
# parámetro devuelve la conversión a SQLAlchemy, que la hace igual en todos
# los motores.
_MOMENT = DateTime(timezone=True)

# Los tipos de turno están escritos a mano porque el dominio de `availability`
# no se puede importar desde acá. En uno de atención se reciben citas; en una
# guardia se cubren las emergencias.
_REGULAR = "regular"
_ON_CALL = "on_call"

_PET_IS_OWNED = text(
    "SELECT 1 FROM pets WHERE id = :pet_id AND owner_id = :owner_id AND is_active = :active"
)

_PET_NAME = text("SELECT name FROM pets WHERE id = :pet_id")

_CLIENT_CONTACT = text("SELECT first_name, last_name, phone FROM users WHERE id = :client_id")

_SCHEDULE_COVERS = text(
    "SELECT 1 FROM availability_slots "
    "WHERE veterinarian_id = :veterinarian_id AND kind = :kind "
    "AND starts_at <= :starts_at AND ends_at >= :ends_at "
    "LIMIT 1"
).bindparams(
    bindparam("starts_at", type_=_MOMENT),
    bindparam("ends_at", type_=_MOMENT),
)

_WORKING_AT = text(
    "SELECT DISTINCT s.veterinarian_id FROM availability_slots s "
    "JOIN users u ON u.id = s.veterinarian_id "
    "WHERE u.role = :role AND u.is_active = :active AND s.kind = :kind "
    "AND s.starts_at <= :moment AND s.ends_at > :moment"
).bindparams(bindparam("moment", type_=_MOMENT))

# Turnos de atención que tocan la ventana. Una guardia no se ofrece para
# reservar: está para las emergencias.
_BOOKABLE_SLOTS = text(
    "SELECT s.veterinarian_id, s.starts_at, s.ends_at FROM availability_slots s "
    "JOIN users u ON u.id = s.veterinarian_id "
    "WHERE u.role = :role AND u.is_active = :active AND s.kind = :kind "
    "AND s.ends_at > :starts_at AND s.starts_at < :ends_at "
    "ORDER BY s.starts_at"
).bindparams(
    bindparam("starts_at", type_=_MOMENT),
    bindparam("ends_at", type_=_MOMENT),
)

# Una sola consulta para toda la página de citas, no una por fila. Los
# `LEFT JOIN` dejan la cita en la respuesta aunque falte un dato ajeno.
_LABELS = text(
    "SELECT a.id, p.name AS pet_name, "
    "c.first_name AS client_first, c.last_name AS client_last, "
    "v.first_name AS vet_first, v.last_name AS vet_last, "
    "t.name AS type_name, t.is_emergency "
    "FROM appointments a "
    "LEFT JOIN pets p ON p.id = a.pet_id "
    "LEFT JOIN users c ON c.id = a.client_id "
    "LEFT JOIN users v ON v.id = a.veterinarian_id "
    "LEFT JOIN appointment_types t ON t.id = a.appointment_type_id "
    "WHERE a.id IN :ids"
).bindparams(bindparam("ids", expanding=True))

_IS_BOOKABLE = text(
    "SELECT 1 FROM users WHERE id = :veterinarian_id AND role = :role AND is_active = :active"
)


class SqlPetDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def is_owned_by(self, pet_id: int, owner_id: int) -> bool:
        # Una mascota dada de baja no puede recibir citas nuevas.
        row = (
            await self._session.execute(
                _PET_IS_OWNED, {"pet_id": pet_id, "owner_id": owner_id, "active": True}
            )
        ).first()
        return row is not None

    async def find_name(self, pet_id: int) -> str | None:
        row = (await self._session.execute(_PET_NAME, {"pet_id": pet_id})).first()
        return row.name if row else None


def _full_name(first: str | None, last: str | None) -> str:
    return f"{first or ''} {last or ''}".strip()


class SqlAppointmentLabelDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def labels_for(self, appointment_ids: list[int]) -> dict[int, AppointmentLabels]:
        if not appointment_ids:
            return {}
        rows = await self._session.execute(_LABELS, {"ids": sorted(set(appointment_ids))})
        return {
            int(row.id): AppointmentLabels(
                pet_name=row.pet_name or "",
                client_name=_full_name(row.client_first, row.client_last),
                veterinarian_name=_full_name(row.vet_first, row.vet_last),
                appointment_type_name=row.type_name or "",
                is_emergency=bool(row.is_emergency),
            )
            for row in rows
        }


class SqlClientDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_contact(self, client_id: int) -> ClientContact | None:
        row = (await self._session.execute(_CLIENT_CONTACT, {"client_id": client_id})).first()
        if row is None:
            return None
        return ClientContact(name=f"{row.first_name} {row.last_name}".strip(), phone=row.phone)


class SqlScheduleDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bookable_slots_between(
        self, starts_at: datetime, ends_at: datetime
    ) -> list[ScheduleSlot]:
        rows = await self._session.execute(
            _BOOKABLE_SLOTS.columns(
                column("veterinarian_id", Integer),
                column("starts_at", _MOMENT),
                column("ends_at", _MOMENT),
            ),
            {
                "role": Role.VETERINARIAN.value,
                "active": True,
                "kind": _REGULAR,
                "starts_at": starts_at,
                "ends_at": ends_at,
            },
        )
        return [
            ScheduleSlot(
                veterinarian_id=int(row.veterinarian_id),
                starts_at=_as_utc(row.starts_at),
                ends_at=_as_utc(row.ends_at),
            )
            for row in rows
        ]

    async def covers(self, veterinarian_id: int, starts_at: datetime, ends_at: datetime) -> bool:
        """La cita entera tiene que caber dentro de un único turno de atención.

        Repartirla entre dos turnos contiguos seria defendible, pero el
        original tampoco lo hacia y abre la puerta a agendar sobre el hueco
        entre dos jornadas.
        """
        row = (
            await self._session.execute(
                _SCHEDULE_COVERS,
                {
                    "veterinarian_id": veterinarian_id,
                    "kind": _REGULAR,
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                },
            )
        ).first()
        return row is not None

    async def veterinarians_on_duty(self, moment: datetime) -> list[int]:
        return await self._working_at(moment, _ON_CALL)

    async def veterinarians_working(self, moment: datetime) -> list[int]:
        return await self._working_at(moment, _REGULAR)

    async def _working_at(self, moment: datetime, kind: str) -> list[int]:
        rows = await self._session.execute(
            _WORKING_AT,
            {"role": Role.VETERINARIAN.value, "active": True, "kind": kind, "moment": moment},
        )
        return [int(row.veterinarian_id) for row in rows]

    async def is_bookable_for_normal_appointments(self, veterinarian_id: int) -> bool:
        """Solo un veterinario con la cuenta activa recibe citas.

        Que además tenga turno a esa hora lo comprueba `covers`.
        """
        row = (
            await self._session.execute(
                _IS_BOOKABLE,
                {
                    "veterinarian_id": veterinarian_id,
                    "role": Role.VETERINARIAN.value,
                    "active": True,
                },
            )
        ).first()
        return row is not None
