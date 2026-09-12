"""Adaptador de entrada HTTP para los pagos.

Registrar y anular un pago es cosa del personal de la clínica. Verlos, no: un
cliente ve los suyos, y por eso el listado alcanza con estar autenticado y
recorta según el rol, no según el endpoint.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import PrincipalDep, require_roles
from gestvet.core.identity import STAFF_ROLES, Principal, Role
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.modules.billing.adapters.api.dependencies import (
    AppointmentDirectoryDep,
    PaymentRepositoryDep,
)
from gestvet.modules.billing.adapters.api.schemas import (
    MethodTotalResponse,
    PaymentPageResponse,
    PaymentReportResponse,
    PaymentResponse,
    RegisterPaymentRequest,
    VoidPaymentRequest,
)
from gestvet.modules.billing.domain.entities import PaymentMethod
from gestvet.modules.billing.domain.exceptions import (
    AppointmentNotFound,
    InvalidPayment,
    PaymentAlreadyVoided,
    PaymentNotFound,
)
from gestvet.modules.billing.ports.payment_repository import PaymentQuery
from gestvet.modules.billing.use_cases.build_payment_report import BuildPaymentReport
from gestvet.modules.billing.use_cases.list_payments import ListPayments, scope_to
from gestvet.modules.billing.use_cases.register_payment import (
    RegisterPayment,
    RegisterPaymentCommand,
)
from gestvet.modules.billing.use_cases.void_payment import VoidPayment, VoidPaymentCommand

router = APIRouter()

StaffDep = Annotated[Principal, Depends(require_roles(*STAFF_ROLES))]


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un pago",
)
async def register_payment(
    payload: RegisterPaymentRequest,
    staff: StaffDep,
    payments: PaymentRepositoryDep,
    appointments: AppointmentDirectoryDep,
    activity: ActivityRecorderDep,
) -> PaymentResponse:
    try:
        payment = await RegisterPayment(payments, appointments, activity)(
            RegisterPaymentCommand(
                appointment_id=payload.appointment_id,
                amount=payload.amount,
                method=payload.method,
                registered_by=staff.user_id,
                reference=payload.reference,
                notes=payload.notes,
            )
        )
    except AppointmentNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidPayment as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return PaymentResponse.from_entity(payment)


@router.post(
    "/{payment_id}/void",
    response_model=PaymentResponse,
    summary="Anular un pago registrado por error",
)
async def void_payment(
    payment_id: int,
    payload: VoidPaymentRequest,
    staff: StaffDep,
    payments: PaymentRepositoryDep,
    activity: ActivityRecorderDep,
) -> PaymentResponse:
    try:
        payment = await VoidPayment(payments, activity)(
            VoidPaymentCommand(payment_id=payment_id, actor_id=staff.user_id, reason=payload.reason)
        )
    except PaymentNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except (PaymentAlreadyVoided, InvalidPayment) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return PaymentResponse.from_entity(payment)


@router.get("", response_model=PaymentPageResponse, summary="Listar pagos")
async def list_payments(
    principal: PrincipalDep,
    payments: PaymentRepositoryDep,
    appointment_id: Annotated[int | None, Query(ge=1)] = None,
    method: Annotated[PaymentMethod | None, Query(description="Filtra por medio")] = None,
    include_voided: Annotated[bool, Query(description="Incluye los anulados")] = True,
    starts_after: Annotated[datetime | None, Query(description="Desde")] = None,
    ends_before: Annotated[datetime | None, Query(description="Hasta")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaymentPageResponse:
    # El recorte se decide en el caso de uso, no acá: un filtro que llega del
    # cliente nunca amplía el conjunto, solo lo estrecha.
    query = scope_to(
        principal,
        PaymentQuery(
            appointment_id=appointment_id,
            method=method,
            include_voided=include_voided,
            starts_after=starts_after,
            ends_before=ends_before,
            limit=limit,
            offset=offset,
        ),
    )
    page = await ListPayments(payments)(query)
    return PaymentPageResponse(
        items=[PaymentResponse.from_entity(item) for item in page.items],
        total=page.total,
    )


@router.get(
    "/report",
    response_model=PaymentReportResponse,
    dependencies=[Depends(require_roles(Role.ADMIN))],
    summary="Cuánto se cobró y por qué medio",
)
async def payment_report(
    payments: PaymentRepositoryDep,
    starts_after: Annotated[datetime | None, Query(description="Desde")] = None,
    ends_before: Annotated[datetime | None, Query(description="Hasta")] = None,
) -> PaymentReportResponse:
    items = await BuildPaymentReport(payments)(starts_after=starts_after, ends_before=ends_before)
    return PaymentReportResponse(
        items=[MethodTotalResponse.from_entity(item) for item in items],
        grand_total=sum((item.total for item in items), start=Decimal(0)),
    )
