from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.pagination import Page
from gestvet.modules.appointments.adapters.persistence.mappers import (
    entity_to_row,
    row_to_entity,
    type_row_to_entity,
)
from gestvet.modules.appointments.adapters.persistence.models import (
    AppointmentRow,
    AppointmentTypeRow,
)
from gestvet.modules.appointments.domain.entities import (
    ACTIVE_STATUSES,
    MAX_APPOINTMENT_DURATION,
    TURNAROUND,
    Appointment,
    AppointmentType,
)
from gestvet.modules.appointments.ports.repositories import AppointmentQuery

_ACTIVE_VALUES = [status.value for status in ACTIVE_STATUSES]


class SqlAlchemyAppointmentTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, type_id: int) -> AppointmentType | None:
        row = await self._session.get(AppointmentTypeRow, type_id)
        return type_row_to_entity(row) if row else None

    async def list_active(self, include_emergency: bool = False) -> list[AppointmentType]:
        statement = select(AppointmentTypeRow).where(AppointmentTypeRow.is_active.is_(True))
        if not include_emergency:
            # El original escribía `WHERE id != 8` en cada consulta.
            statement = statement.where(AppointmentTypeRow.is_emergency.is_(False))
        rows = await self._session.execute(statement.order_by(AppointmentTypeRow.name))
        return [type_row_to_entity(row) for row in rows.scalars().all()]

    async def get_emergency(self) -> AppointmentType | None:
        rows = await self._session.execute(
            select(AppointmentTypeRow)
            .where(
                AppointmentTypeRow.is_emergency.is_(True),
                AppointmentTypeRow.is_active.is_(True),
            )
            .limit(1)
        )
        row = rows.scalar_one_or_none()
        return type_row_to_entity(row) if row else None


class SqlAlchemyAppointmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, appointment: Appointment) -> Appointment:
        row = entity_to_row(appointment)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def get(self, appointment_id: int) -> Appointment | None:
        row = await self._session.get(AppointmentRow, appointment_id)
        return row_to_entity(row) if row else None

    async def save(self, appointment: Appointment) -> Appointment:
        row = await self._session.get(AppointmentRow, appointment.id)
        if row is None:
            raise ValueError(f"La cita {appointment.id} ya no existe.")
        row.status = appointment.status.value
        row.cancellation_reason = appointment.cancellation_reason
        row.updated_by = appointment.updated_by
        row.description = appointment.description
        row.reminder_sent_at = appointment.reminder_sent_at
        await self._session.flush()
        return row_to_entity(row)

    async def search(self, query: AppointmentQuery) -> Page[Appointment]:
        base = self._apply_filters(select(AppointmentRow), query)

        total = int(
            (
                await self._session.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
        )
        rows = await self._session.execute(
            base.order_by(AppointmentRow.scheduled_at.desc(), AppointmentRow.id)
            .limit(query.limit)
            .offset(query.offset)
        )
        return Page(items=[row_to_entity(row) for row in rows.scalars().all()], total=total)

    async def find_conflicting(
        self, veterinarian_id: int, starts_at: datetime, ends_at: datetime
    ) -> list[Appointment]:
        """Citas activas del veterinario que pisan la ventana pedida.

        El fin de una cita es `scheduled_at + duracion`, y la duración se
        guarda en minutos porque INTERVAL no existe en SQLite. Sumar eso dentro
        del SQL obligaría a escribir una consulta distinta por motor.

        En vez de eso la consulta acota por el único dato indexado, la fecha de
        inicio, usando el techo de duración para no dejar fuera a ninguna
        candidata, y el solapamiento exacto lo decide la entidad. La ventana es
        de horas, así que son pocas filas.
        """
        earliest = starts_at - MAX_APPOINTMENT_DURATION - TURNAROUND
        rows = await self._session.execute(
            select(AppointmentRow).where(
                AppointmentRow.veterinarian_id == veterinarian_id,
                AppointmentRow.status.in_(_ACTIVE_VALUES),
                AppointmentRow.scheduled_at >= earliest,
                AppointmentRow.scheduled_at < ends_at + TURNAROUND,
            )
        )
        candidatas = [row_to_entity(row) for row in rows.scalars().all()]
        return [cita for cita in candidatas if cita.overlaps(starts_at, ends_at)]

    async def find_due_for_reminder(
        self, window_start: datetime, window_end: datetime
    ) -> list[Appointment]:
        """Citas confirmadas que entran a la ventana de 24h y nunca avisaron.

        `reminder_sent_at IS NULL` es lo que evita mandar el mismo mensaje dos
        veces si el proceso periódico las vuelve a mirar en la siguiente
        vuelta, antes de que la ventana termine de pasar.
        """
        rows = await self._session.execute(
            select(AppointmentRow).where(
                AppointmentRow.status == "confirmed",
                AppointmentRow.reminder_sent_at.is_(None),
                AppointmentRow.scheduled_at >= window_start,
                AppointmentRow.scheduled_at < window_end,
            )
        )
        return [row_to_entity(row) for row in rows.scalars().all()]

    async def count_active_for(self, veterinarian_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AppointmentRow)
            .where(
                AppointmentRow.veterinarian_id == veterinarian_id,
                AppointmentRow.status.in_(_ACTIVE_VALUES),
            )
        )
        return int(result.scalar_one())

    def _apply_filters(
        self, statement: Select[tuple[AppointmentRow]], query: AppointmentQuery
    ) -> Select[tuple[AppointmentRow]]:
        if query.client_id is not None:
            statement = statement.where(AppointmentRow.client_id == query.client_id)
        if query.veterinarian_id is not None:
            statement = statement.where(AppointmentRow.veterinarian_id == query.veterinarian_id)
        if query.pet_id is not None:
            statement = statement.where(AppointmentRow.pet_id == query.pet_id)
        if query.statuses:
            statement = statement.where(
                AppointmentRow.status.in_([status.value for status in query.statuses])
            )
        if query.is_emergency is not None:
            statement = statement.join(
                AppointmentTypeRow,
                AppointmentTypeRow.id == AppointmentRow.appointment_type_id,
            ).where(AppointmentTypeRow.is_emergency.is_(query.is_emergency))
        if query.starts_after is not None:
            statement = statement.where(AppointmentRow.scheduled_at >= query.starts_after)
        if query.ends_before is not None:
            statement = statement.where(AppointmentRow.scheduled_at < query.ends_before)
        return statement
