"""Caso de uso: listar pagos.

Un cliente ve los suyos, dónde sea que estén: el `client_id` queda grabado en
el pago desde que se registra, así que no hace falta preguntarle a
`appointments` de quién es cada cita para acotar el listado.
"""

from __future__ import annotations

from dataclasses import replace

from gestvet.core.identity import Principal, Role
from gestvet.core.pagination import Page
from gestvet.modules.billing.domain.entities import Payment
from gestvet.modules.billing.ports.payment_repository import PaymentQuery, PaymentRepository


class ListPayments:
    def __init__(self, payments: PaymentRepository) -> None:
        self._payments = payments

    async def __call__(self, query: PaymentQuery) -> Page[Payment]:
        return await self._payments.search(query)


def scope_to(principal: Principal, query: PaymentQuery) -> PaymentQuery:
    """Recorta la búsqueda a lo que este usuario tiene derecho a ver.

    Se aplica sobre el criterio, no sobre el resultado: un filtro que llega
    del cliente nunca puede ampliar el conjunto, solo estrecharlo.
    """
    if principal.role is Role.CLIENT:
        return replace(query, client_id=principal.user_id)
    return query
