from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.pagination import Page
from gestvet.modules.billing.adapters.persistence.mappers import (
    entity_to_row,
    qr_charge_entity_to_row,
    qr_charge_row_to_entity,
    row_to_entity,
)
from gestvet.modules.billing.adapters.persistence.models import PaymentRow, QrChargeRow
from gestvet.modules.billing.domain.entities import Payment, PaymentMethod
from gestvet.modules.billing.domain.qr_charge import QrCharge
from gestvet.modules.billing.ports.payment_repository import MethodTotal, PaymentQuery


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, payment: Payment) -> Payment:
        row = entity_to_row(payment)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def get(self, payment_id: int) -> Payment | None:
        row = await self._session.get(PaymentRow, payment_id)
        return row_to_entity(row) if row else None

    async def save(self, payment: Payment) -> Payment:
        row = await self._session.get(PaymentRow, payment.id)
        if row is None:
            raise ValueError(f"El pago {payment.id} ya no existe.")
        row.voided_at = payment.voided_at
        row.void_reason = payment.void_reason
        await self._session.flush()
        return row_to_entity(row)

    async def search(self, query: PaymentQuery) -> Page[Payment]:
        base = self._apply_filters(select(PaymentRow), query)

        total = int(
            (
                await self._session.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
        )
        rows = await self._session.execute(
            base.order_by(PaymentRow.paid_at.desc(), PaymentRow.id.desc())
            .limit(query.limit)
            .offset(query.offset)
        )
        return Page(items=[row_to_entity(row) for row in rows.scalars().all()], total=total)

    async def totals_by_method(self, query: PaymentQuery) -> list[MethodTotal]:
        base = self._apply_filters(
            select(
                PaymentRow.method,
                func.sum(PaymentRow.amount),
                func.count(),
            ).group_by(PaymentRow.method),
            query,
        )
        rows = await self._session.execute(base)
        return [
            MethodTotal(method=PaymentMethod(method), total=total or 0, count=count)
            for method, total, count in rows.all()
        ]

    def _apply_filters(self, statement: Select, query: PaymentQuery) -> Select:
        if query.appointment_id is not None:
            statement = statement.where(PaymentRow.appointment_id == query.appointment_id)
        if query.client_id is not None:
            statement = statement.where(PaymentRow.client_id == query.client_id)
        if query.method is not None:
            statement = statement.where(PaymentRow.method == query.method.value)
        if not query.include_voided:
            statement = statement.where(PaymentRow.voided_at.is_(None))
        if query.starts_after is not None:
            statement = statement.where(PaymentRow.paid_at >= query.starts_after)
        if query.ends_before is not None:
            statement = statement.where(PaymentRow.paid_at < query.ends_before)
        return statement


class SqlAlchemyQrChargeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, charge: QrCharge) -> QrCharge:
        row = qr_charge_entity_to_row(charge)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return qr_charge_row_to_entity(row)

    async def get(self, charge_id: int) -> QrCharge | None:
        row = await self._session.get(QrChargeRow, charge_id)
        return qr_charge_row_to_entity(row) if row else None

    async def save(self, charge: QrCharge) -> QrCharge:
        row = await self._session.get(QrChargeRow, charge.id)
        if row is None:
            raise ValueError(f"El cobro {charge.id} ya no existe.")
        row.status = charge.status.value
        row.payment_id = charge.payment_id
        row.confirmed_at = charge.confirmed_at
        await self._session.flush()
        return qr_charge_row_to_entity(row)

    async def find_latest_for_appointment(self, appointment_id: int) -> QrCharge | None:
        row = (
            await self._session.execute(
                select(QrChargeRow)
                .where(QrChargeRow.appointment_id == appointment_id)
                .order_by(QrChargeRow.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return qr_charge_row_to_entity(row) if row else None
